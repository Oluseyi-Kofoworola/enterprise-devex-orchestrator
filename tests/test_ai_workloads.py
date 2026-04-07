"""Tests for AI/Foundry workload support across the orchestrator."""

from __future__ import annotations

from src.orchestrator.agents.intent_parser import IntentParserAgent
from src.orchestrator.agents.architecture_planner import ArchitecturePlannerAgent
from src.orchestrator.agents.governance_reviewer import GovernanceReviewerAgent
from src.orchestrator.config import AppConfig, AzureConfig, CopilotConfig, LLMConfig
from src.orchestrator.generators.app_generator import AppGenerator
from src.orchestrator.generators.bicep_generator import BicepGenerator
from src.orchestrator.generators.frontend_generator import FrontendGenerator
from src.orchestrator.intent_schema import (
    AppType,
    AuthModel,
    CICDRequirements,
    ComplianceFramework,
    ComponentSpec,
    DataStore,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    PlanOutput,
    SecurityRequirements,
    ThreatEntry,
)
from src.orchestrator.standards.naming import NamingEngine, ResourceType
from src.orchestrator.tools.policy_engine import POLICY_CATALOG, list_policies


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


def _make_ai_spec(
    app_type: AppType = AppType.AI_APP,
    ai_features: list[str] | None = None,
    data_stores: list[DataStore] | None = None,
    ai_model: str = "gpt-4o",
) -> IntentSpec:
    return IntentSpec(
        project_name="test-ai-app",
        app_type=app_type,
        description="An AI-powered application",
        raw_intent="Build an AI chatbot with RAG",
        data_stores=data_stores or [DataStore.AI_SEARCH],
        uses_ai=True,
        ai_model=ai_model,
        ai_features=ai_features or ["chat", "rag"],
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
        confidence=0.9,
    )


def _make_ai_plan() -> PlanOutput:
    return PlanOutput(
        title="AI Architecture Plan",
        summary="AI-powered application architecture",
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
                security_controls=["RBAC", "Soft delete"],
            ),
            ComponentSpec(
                name="log-analytics",
                azure_service="Microsoft.OperationalInsights/workspaces",
                purpose="Centralized logging",
                bicep_module="log-analytics.bicep",
                security_controls=[],
            ),
            ComponentSpec(
                name="managed-identity",
                azure_service="Microsoft.ManagedIdentity/userAssignedIdentities",
                purpose="Authentication",
                bicep_module="managed-identity.bicep",
                security_controls=["RBAC"],
            ),
            ComponentSpec(
                name="container-registry",
                azure_service="Microsoft.ContainerRegistry/registries",
                purpose="Container images",
                bicep_module="container-registry.bicep",
                security_controls=["AcrPull role"],
            ),
            ComponentSpec(
                name="azure-openai",
                azure_service="Microsoft.CognitiveServices/accounts",
                purpose="AI model hosting",
                bicep_module="openai.bicep",
                security_controls=["Managed Identity", "Content filtering"],
            ),
            ComponentSpec(
                name="ai-search",
                azure_service="Microsoft.Search/searchServices",
                purpose="Vector search for RAG",
                bicep_module="ai-search.bicep",
                security_controls=["RBAC", "Managed Identity"],
            ),
        ],
        decisions=[],
        threat_model=[
            ThreatEntry(
                id="T-001", category="Spoofing",
                description="Identity spoofing", mitigation="Managed Identity",
                residual_risk="Low",
            ),
            ThreatEntry(
                id="T-002", category="Tampering",
                description="Data tampering", mitigation="Encryption",
                residual_risk="Low",
            ),
            ThreatEntry(
                id="T-003", category="Information Disclosure",
                description="AI data leakage from training data or system prompts",
                mitigation="Content filtering, system prompt isolation",
                residual_risk="Medium",
            ),
            ThreatEntry(
                id="T-004", category="Denial of Service",
                description="Token exhaustion and cost explosion",
                mitigation="Rate limiting, token budgets, per-user quotas",
                residual_risk="Medium",
            ),
        ],
        diagram_mermaid="graph TD; A-->B;",
    )


# ===================================================================
# Intent Parser -- AI Detection
# ===================================================================


class TestIntentParserAI:
    """Test AI intent detection and feature extraction."""

    def setup_method(self) -> None:
        self.parser = IntentParserAgent(_make_config())

    def test_detects_ai_agent_app_type(self) -> None:
        spec = self.parser.parse("Build an agentic AI system that autonomously processes documents")
        assert spec.app_type == AppType.AI_AGENT

    def test_detects_ai_app_type(self) -> None:
        spec = self.parser.parse("Build a chatbot powered by LLM for customer support")
        assert spec.app_type == AppType.AI_APP

    def test_detects_ai_app_from_copilot_keyword(self) -> None:
        spec = self.parser.parse("Build an enterprise copilot for internal knowledge retrieval")
        assert spec.app_type == AppType.AI_APP

    def test_uses_ai_flag_set_for_ai_types(self) -> None:
        spec = self.parser.parse("Build an AI chatbot with Azure OpenAI")
        assert spec.uses_ai is True

    def test_detects_ai_search_data_store(self) -> None:
        spec = self.parser.parse("Build a chatbot with vector search for RAG retrieval")
        assert DataStore.AI_SEARCH in spec.data_stores

    def test_auto_adds_ai_search_for_rag(self) -> None:
        spec = self.parser.parse("Build an AI app with RAG grounding from documents")
        assert DataStore.AI_SEARCH in spec.data_stores

    def test_detects_chat_feature(self) -> None:
        spec = self.parser.parse("Build a chatbot with Azure OpenAI for conversations")
        assert "chat" in spec.ai_features

    def test_detects_rag_feature(self) -> None:
        spec = self.parser.parse("Build an AI app with RAG retrieval from documents")
        assert "rag" in spec.ai_features

    def test_detects_embeddings_feature(self) -> None:
        spec = self.parser.parse("Build an AI system with embeddings for semantic search")
        assert "embeddings" in spec.ai_features

    def test_detects_agents_feature(self) -> None:
        spec = self.parser.parse("Build an agentic AI system with tool calling")
        assert "agents" in spec.ai_features

    def test_detects_content_safety_feature(self) -> None:
        spec = self.parser.parse("Build an AI chatbot with content safety and moderation")
        assert "content-safety" in spec.ai_features

    def test_detects_gpt4o_model(self) -> None:
        spec = self.parser.parse("Build a chatbot using gpt-4o for conversations")
        assert spec.ai_model == "gpt-4o"

    def test_detects_gpt4o_mini_model(self) -> None:
        spec = self.parser.parse("Build a chatbot using gpt-4o-mini for conversations")
        assert spec.ai_model == "gpt-4o-mini"

    def test_non_ai_intent_no_ai_features(self) -> None:
        spec = self.parser.parse("Build a REST API with blob storage")
        assert spec.ai_features == []
        assert spec.app_type != AppType.AI_APP
        assert spec.app_type != AppType.AI_AGENT


# ===================================================================
# Architecture Planner -- AI Components
# ===================================================================


class TestArchitecturePlannerAI:
    """Test AI component generation in architecture planner."""

    def setup_method(self) -> None:
        self.planner = ArchitecturePlannerAgent(_make_config())

    def test_ai_plan_has_openai_component(self) -> None:
        spec = _make_ai_spec()
        plan = self.planner.plan(spec)
        component_names = {c.name for c in plan.components}
        assert "azure-openai" in component_names

    def test_ai_plan_has_ai_search_component(self) -> None:
        spec = _make_ai_spec(data_stores=[DataStore.AI_SEARCH])
        plan = self.planner.plan(spec)
        component_names = {c.name for c in plan.components}
        assert "ai-search" in component_names

    def test_ai_plan_has_ai_threats(self) -> None:
        spec = _make_ai_spec()
        plan = self.planner.plan(spec)
        threat_texts = " ".join(t.description.lower() for t in plan.threat_model)
        assert "ai" in threat_texts or "token" in threat_texts or "prompt" in threat_texts

    def test_ai_plan_has_ai_decisions(self) -> None:
        spec = _make_ai_spec()
        plan = self.planner.plan(spec)
        decision_ids = {d.id for d in plan.decisions}
        assert "ADR-006" in decision_ids  # AI decision

    def test_ai_plan_diagram_has_ai_services(self) -> None:
        spec = _make_ai_spec()
        plan = self.planner.plan(spec)
        assert "OpenAI" in plan.diagram_mermaid or "AI" in plan.diagram_mermaid

    def test_non_ai_plan_no_openai(self) -> None:
        spec = _make_ai_spec(app_type=AppType.API)
        spec.uses_ai = False
        spec.ai_features = []
        plan = self.planner.plan(spec)
        component_names = {c.name for c in plan.components}
        assert "azure-openai" not in component_names


# ===================================================================
# Bicep Generator -- AI Modules
# ===================================================================


class TestBicepGeneratorAI:
    """Test AI Bicep module generation."""

    def setup_method(self) -> None:
        self.gen = BicepGenerator()

    def test_generates_openai_bicep(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec, _make_ai_plan())
        assert "infra/bicep/modules/openai.bicep" in files

    def test_openai_bicep_has_cognitive_services(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec, _make_ai_plan())
        openai = files["infra/bicep/modules/openai.bicep"]
        assert "Microsoft.CognitiveServices/accounts" in openai

    def test_openai_bicep_has_model_deployment(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec, _make_ai_plan())
        openai = files["infra/bicep/modules/openai.bicep"]
        assert "deployments" in openai

    def test_openai_bicep_has_rbac(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec, _make_ai_plan())
        openai = files["infra/bicep/modules/openai.bicep"]
        assert "roleAssignments" in openai or "roleDefinitionId" in openai

    def test_openai_bicep_has_diagnostics(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec, _make_ai_plan())
        openai = files["infra/bicep/modules/openai.bicep"]
        assert "diagnosticSettings" in openai

    def test_generates_ai_search_bicep(self) -> None:
        spec = _make_ai_spec(data_stores=[DataStore.AI_SEARCH])
        files = self.gen.generate(spec, _make_ai_plan())
        assert "infra/bicep/modules/ai-search.bicep" in files

    def test_ai_search_bicep_has_search_service(self) -> None:
        spec = _make_ai_spec(data_stores=[DataStore.AI_SEARCH])
        files = self.gen.generate(spec, _make_ai_plan())
        search = files["infra/bicep/modules/ai-search.bicep"]
        assert "Microsoft.Search/searchServices" in search

    def test_ai_search_bicep_has_semantic_search(self) -> None:
        spec = _make_ai_spec(data_stores=[DataStore.AI_SEARCH])
        files = self.gen.generate(spec, _make_ai_plan())
        search = files["infra/bicep/modules/ai-search.bicep"]
        assert "semantic" in search.lower()

    def test_main_bicep_includes_ai_modules(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec, _make_ai_plan())
        main = files["infra/bicep/main.bicep"]
        assert "openai" in main.lower()

    def test_no_ai_modules_for_non_ai_spec(self) -> None:
        from tests.test_generators import _make_spec, _make_plan
        files = self.gen.generate(_make_spec(), _make_plan())
        assert "infra/bicep/modules/openai.bicep" not in files
        assert "infra/bicep/modules/ai-search.bicep" not in files


# ===================================================================
# App Generator -- AI SDK Integration
# ===================================================================


class TestAppGeneratorAI:
    """Test AI SDK code generation."""

    def setup_method(self) -> None:
        self.gen = AppGenerator()

    def test_generates_ai_client(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        assert "src/app/ai/client.py" in files

    def test_ai_client_uses_managed_identity(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        client = files["src/app/ai/client.py"]
        assert "DefaultAzureCredential" in client
        assert "get_bearer_token_provider" in client

    def test_ai_client_no_api_key(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        client = files["src/app/ai/client.py"]
        # Must not contain hardcoded API key values; env-var lookups are fine
        assert 'api_key="' not in client and "api_key='" not in client

    def test_generates_ai_chat_router(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        assert "src/app/ai/chat.py" in files

    def test_chat_router_has_endpoint(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        chat = files["src/app/ai/chat.py"]
        assert "/chat" in chat
        assert "router" in chat.lower()

    def test_generates_ai_agent(self) -> None:
        spec = _make_ai_spec(ai_features=["chat", "agents"])
        files = self.gen.generate(spec)
        assert "src/app/ai/agent.py" in files

    def test_ai_agent_has_semantic_kernel(self) -> None:
        spec = _make_ai_spec(ai_features=["chat", "agents"])
        files = self.gen.generate(spec)
        agent = files["src/app/ai/agent.py"]
        assert "semantic_kernel" in agent or "Kernel" in agent

    def test_requirements_has_ai_sdks(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        reqs = files["src/app/requirements.txt"]
        assert "openai" in reqs

    def test_requirements_has_search_sdk_for_rag(self) -> None:
        spec = _make_ai_spec(ai_features=["chat", "rag"], data_stores=[DataStore.AI_SEARCH])
        files = self.gen.generate(spec)
        reqs = files["src/app/requirements.txt"]
        assert "azure-search-documents" in reqs

    def test_main_mounts_ai_router(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        main = files["src/app/main.py"]
        assert "ai" in main.lower()

    def test_no_ai_files_for_non_ai_spec(self) -> None:
        from tests.test_generators import _make_spec
        files = self.gen.generate(_make_spec())
        assert "src/app/ai/client.py" not in files
        assert "src/app/ai/chat.py" not in files


# ===================================================================
# Frontend Generator -- Chat Page
# ===================================================================


class TestFrontendGeneratorAI:
    """Test AI chat page generation."""

    def setup_method(self) -> None:
        self.gen = FrontendGenerator()

    def test_generates_chat_page(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        chat_files = [f for f in files if "Chat" in f or "chat" in f.lower()]
        assert len(chat_files) > 0

    def test_chat_page_has_message_handling(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        chat_files = {k: v for k, v in files.items() if "Chat" in k}
        if chat_files:
            content = list(chat_files.values())[0]
            assert "message" in content.lower()
            assert "send" in content.lower() or "submit" in content.lower()

    def test_app_tsx_has_chat_route(self) -> None:
        spec = _make_ai_spec()
        files = self.gen.generate(spec)
        app_tsx = files.get("frontend/src/App.tsx", "")
        assert "chat" in app_tsx.lower()

    def test_no_chat_page_for_non_ai(self) -> None:
        from tests.test_generators import _make_spec
        spec = _make_spec()
        files = self.gen.generate(spec)
        chat_files = [f for f in files if "ChatPage" in f]
        assert len(chat_files) == 0


# ===================================================================
# Governance Reviewer -- AI Checks
# ===================================================================


class TestGovernanceReviewerAI:
    """Test AI governance checks."""

    def setup_method(self) -> None:
        self.reviewer = GovernanceReviewerAgent(_make_config())

    def test_ai_workload_runs_ai_checks(self) -> None:
        spec = _make_ai_spec()
        plan = _make_ai_plan()
        report = self.reviewer.validate_plan(spec, plan)
        ai_checks = [c for c in report.checks if c.check_id.startswith("AI-")]
        assert len(ai_checks) > 0

    def test_ai_governance_passes_with_all_components(self) -> None:
        spec = _make_ai_spec()
        plan = _make_ai_plan()
        report = self.reviewer.validate_plan(spec, plan)
        ai_checks = [c for c in report.checks if c.check_id.startswith("AI-")]
        ai_failures = [c for c in ai_checks if not c.passed]
        assert len(ai_failures) == 0

    def test_ai_governance_fails_missing_openai(self) -> None:
        spec = _make_ai_spec()
        plan = _make_ai_plan()
        # Remove azure-openai from components
        plan.components = [c for c in plan.components if c.name != "azure-openai"]
        report = self.reviewer.validate_plan(spec, plan)
        ai_gov_001 = next((c for c in report.checks if c.check_id == "AI-GOV-001"), None)
        assert ai_gov_001 is not None
        assert ai_gov_001.passed is False

    def test_ai_governance_checks_managed_identity(self) -> None:
        spec = _make_ai_spec()
        plan = _make_ai_plan()
        report = self.reviewer.validate_plan(spec, plan)
        ai_gov_003 = next((c for c in report.checks if c.check_id == "AI-GOV-003"), None)
        assert ai_gov_003 is not None
        assert ai_gov_003.passed is True

    def test_ai_governance_checks_rag_search(self) -> None:
        spec = _make_ai_spec(ai_features=["chat", "rag"])
        plan = _make_ai_plan()
        report = self.reviewer.validate_plan(spec, plan)
        ai_gov_004 = next((c for c in report.checks if c.check_id == "AI-GOV-004"), None)
        assert ai_gov_004 is not None
        assert ai_gov_004.passed is True

    def test_non_ai_workload_no_ai_checks(self) -> None:
        from tests.test_governance_validator import _make_spec, _make_plan
        spec = _make_spec()
        plan = _make_plan()
        report = self.reviewer.validate_plan(spec, plan)
        ai_checks = [c for c in report.checks if c.check_id.startswith("AI-")]
        assert len(ai_checks) == 0


# ===================================================================
# Policy Engine -- AI Policies
# ===================================================================


class TestPolicyEngineAI:
    """Test AI governance policies in the policy engine."""

    def test_ai_policies_in_catalog(self) -> None:
        ai_policies = [p for p in POLICY_CATALOG if p.id.startswith("AI-")]
        assert len(ai_policies) >= 5

    def test_ai_content_safety_policy_exists(self) -> None:
        ai_001 = next((p for p in POLICY_CATALOG if p.id == "AI-001"), None)
        assert ai_001 is not None
        assert "content" in ai_001.name.lower() or "safety" in ai_001.name.lower()

    def test_ai_managed_identity_policy_exists(self) -> None:
        ai_002 = next((p for p in POLICY_CATALOG if p.id == "AI-002"), None)
        assert ai_002 is not None

    def test_ai_rai_documentation_policy_exists(self) -> None:
        ai_004 = next((p for p in POLICY_CATALOG if p.id == "AI-004"), None)
        assert ai_004 is not None


# ===================================================================
# Naming Engine -- AI Resource Types
# ===================================================================


class TestNamingEngineAI:
    """Test AI resource naming conventions."""

    def test_openai_resource_type_exists(self) -> None:
        assert ResourceType.OPENAI.value == "oai"

    def test_ai_search_resource_type_exists(self) -> None:
        assert ResourceType.AI_SEARCH.value == "srch"

    def test_generates_openai_name(self) -> None:
        engine = NamingEngine(workload="myapp", environment="dev", region="eastus2")
        name = engine.generate(ResourceType.OPENAI)
        assert "oai" in name
        assert "myapp" in name

    def test_generates_ai_search_name(self) -> None:
        engine = NamingEngine(workload="myapp", environment="dev", region="eastus2")
        name = engine.generate(ResourceType.AI_SEARCH)
        assert "srch" in name
        assert "myapp" in name


# ===================================================================
# Schema -- AI Fields
# ===================================================================


class TestIntentSchemaAI:
    """Test AI fields in IntentSpec schema."""

    def test_ai_agent_app_type(self) -> None:
        assert AppType.AI_AGENT.value == "ai_agent"

    def test_ai_app_app_type(self) -> None:
        assert AppType.AI_APP.value == "ai_app"

    def test_ai_search_data_store(self) -> None:
        assert DataStore.AI_SEARCH.value == "ai_search"

    def test_default_ai_model(self) -> None:
        spec = IntentSpec(
            project_name="test",
            app_type=AppType.AI_APP,
            description="Test",
            raw_intent="Test",
        )
        assert spec.ai_model == "gpt-4o"

    def test_default_ai_features_empty(self) -> None:
        spec = IntentSpec(
            project_name="test",
            app_type=AppType.API,
            description="Test",
            raw_intent="Test",
        )
        assert spec.ai_features == []

    def test_custom_ai_model(self) -> None:
        spec = IntentSpec(
            project_name="test",
            app_type=AppType.AI_APP,
            description="Test",
            raw_intent="Test",
            ai_model="gpt-4o-mini",
        )
        assert spec.ai_model == "gpt-4o-mini"

    def test_custom_ai_features(self) -> None:
        spec = IntentSpec(
            project_name="test",
            app_type=AppType.AI_APP,
            description="Test",
            raw_intent="Test",
            ai_features=["chat", "rag", "agents"],
        )
        assert "chat" in spec.ai_features
        assert "rag" in spec.ai_features
        assert "agents" in spec.ai_features
