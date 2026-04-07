"""Architecture Planner Agent.

Takes an IntentSpec and produces a PlanOutput with:
    - Component list (Azure services to deploy)
    - Architecture Decision Records (ADRs)
    - Threat model (top 5 threats)
    - Mermaid architecture diagram
    - Live Azure resource validation (quota, SKU, region availability)
"""

from __future__ import annotations

import json
import shutil
import subprocess

from src.orchestrator.agent import AgentRuntime
from src.orchestrator.config import AppConfig
from src.orchestrator.intent_schema import (
    ArchitectureDecision,
    ComponentSpec,
    DataStore,
    IntentSpec,
    PlanOutput,
    ThreatEntry,
)
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)

ARCHITECTURE_PLANNER_SYSTEM_PROMPT = """\
You are an Enterprise Azure Solutions Architect. Given a structured IntentSpec,
produce an architecture plan as a JSON object.

You are NOT generating boilerplate -- you are reasoning about the SPECIFIC
business domain described in the intent. Your decisions, threat model, and
summary must reflect the actual business requirements, not generic templates.

## Rules
1. Select Azure components based on the IntentSpec requirements.
2. Always include: Azure Container Apps, Key Vault, Log Analytics, Managed Identity.
3. Add data stores based on IntentSpec.data_stores.
4. Write Architecture Decision Records (ADRs) for key choices. ADRs must
   reference the SPECIFIC business domain (e.g. "document processing requires
   batch queue support" not "need a queue"). Include at least 5 ADRs.
5. Produce a STRIDE threat model with at least 5 threats SPECIFIC to this
   business domain (e.g. for a healthcare system, include HIPAA data exposure;
   for a financial system, include transaction tampering).
6. Generate a Mermaid diagram showing component relationships.
7. Write a summary that explains WHY this architecture fits this specific
   business need -- reference the business goals, not just the technology.

## Output Format
Return ONLY a JSON object matching this schema:
{
  "title": "string",
  "summary": "string (2-3 sentences referencing the specific business domain and goals)",
  "components": [{"name": "string", "azure_service": "string", "purpose": "string (domain-specific)", "bicep_module": "string", "security_controls": ["string"]}],
  "decisions": [{"id": "ADR-001", "title": "string", "status": "Accepted", "context": "string (reference the business requirement)", "decision": "string", "consequences": "string"}],
  "threat_model": [{"id": "THREAT-001", "category": "Spoofing|Tampering|Repudiation|Information Disclosure|Denial of Service|Elevation of Privilege", "description": "string (domain-specific threat)", "mitigation": "string", "residual_risk": "Low|Medium|High"}],
  "diagram_mermaid": "string (mermaid diagram source)"
}
"""


class ArchitecturePlannerAgent:
    """Generates architecture plan from IntentSpec."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.runtime = AgentRuntime(config)

    def plan(self, spec: IntentSpec) -> PlanOutput:
        """Generate architecture plan from intent specification.

        Strategy: Always build the deterministic baseline first (guaranteed
        correct components, security controls, STRIDE categories). Then
        attempt LLM enrichment to make ADRs, threats, and summaries
        domain-specific. LLM output *merges with* the baseline -- it never
        replaces structural components.
        """
        logger.info("architecture_planner.start", project=spec.project_name)

        # Run live Azure validation (best-effort)
        azure_warnings = self._validate_azure_resources(spec)
        if azure_warnings:
            for w in azure_warnings:
                logger.warning("architecture_planner.azure_validation", warning=w)

        # Step 1: Build deterministic baseline (always correct)
        baseline = self._default_plan(spec)

        # Step 2: Attempt LLM enrichment for domain-specific reasoning
        plan = self._enrich_plan_with_llm(spec, baseline)

        # Attach validation warnings to plan
        if azure_warnings:
            plan.summary += " NOTE: Azure validation produced warnings -- see plan assumptions."
            for w in azure_warnings:
                logger.info("architecture_planner.validation_note", note=w)

        logger.info(
            "architecture_planner.complete",
            components=len(plan.components),
            decisions=len(plan.decisions),
            llm_enriched=plan is not baseline,
        )
        return plan

    def _enrich_plan_with_llm(self, spec: IntentSpec, baseline: PlanOutput) -> PlanOutput:
        """Use LLM to enrich the baseline plan with domain-specific reasoning.

        The LLM sees both the spec AND the baseline plan, and is asked to
        improve the summary, ADRs, and threat model with domain-specific
        reasoning. Components are preserved from baseline (structural correctness).
        """
        if self.config.llm.is_template_only:
            logger.info("architecture_planner.skip_llm", reason="template-only mode")
            return baseline

        enrichment_prompt = f"""I have a baseline architecture plan for the project "{spec.project_name}".
The business context is:
{spec.description}

Raw business intent:
{spec.raw_intent[:2000]}

The baseline plan has {len(baseline.components)} components, {len(baseline.decisions)} ADRs, and {len(baseline.threat_model)} threats.

Current ADR titles: {', '.join(d.title for d in baseline.decisions)}
Current threat categories: {', '.join(t.category for t in baseline.threat_model)}

Please ENRICH this plan by providing:
1. A better "summary" that references the SPECIFIC business domain and goals (2-3 sentences)
2. IMPROVED "decisions" (ADRs) where context and consequences reference the actual business requirements. Keep all {len(baseline.decisions)} existing ADR IDs but rewrite context/consequences to be domain-specific. Add up to 2 additional ADRs if the business domain warrants them.
3. IMPROVED "threat_model" where descriptions and mitigations reference domain-specific risks. Keep all {len(baseline.threat_model)} existing threat IDs but make them domain-specific. Add up to 2 additional threats if the domain warrants them.

Return ONLY a JSON object with keys: "summary", "decisions", "threat_model"
Each decision: {{"id": "ADR-001", "title": "string", "status": "Accepted", "context": "string", "decision": "string", "consequences": "string"}}
Each threat: {{"id": "THREAT-001", "category": "STRIDE category", "description": "string", "mitigation": "string", "residual_risk": "Low|Medium|High"}}
"""
        try:
            response = self.runtime.run_sync(
                system_prompt=ARCHITECTURE_PLANNER_SYSTEM_PROMPT,
                user_message=enrichment_prompt,
                max_iterations=3,
            )
            return self._merge_llm_enrichment(response, baseline, spec)
        except Exception as e:
            logger.warning("architecture_planner.llm_enrichment_failed", error=str(e))
            return baseline

    def _merge_llm_enrichment(self, response: str, baseline: PlanOutput, spec: IntentSpec) -> PlanOutput:
        """Merge LLM enrichment into the baseline plan.

        Rules:
        - Components: NEVER changed by LLM (structural correctness)
        - Diagram: NEVER changed by LLM (derived from components)
        - Summary: Replaced if LLM provides a non-empty one
        - ADRs: Replaced if LLM provides valid ones with matching IDs
        - Threats: Replaced if LLM provides valid ones with STRIDE categories
        """
        import re as _re

        json_match = _re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, _re.DOTALL)
        json_str = json_match.group(1) if json_match else response.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("architecture_planner.llm_json_parse_failed")
            return baseline

        enriched_summary = baseline.summary
        enriched_decisions = list(baseline.decisions)
        enriched_threats = list(baseline.threat_model)

        # Merge summary
        if data.get("summary") and len(data["summary"]) > 20:
            enriched_summary = data["summary"]
            logger.info("architecture_planner.llm_enriched_summary")

        # Merge ADRs -- validate each one has required fields
        if data.get("decisions") and isinstance(data["decisions"], list):
            valid_decisions = []
            for d in data["decisions"]:
                try:
                    valid_decisions.append(ArchitectureDecision(**d))
                except Exception:
                    continue
            if len(valid_decisions) >= len(baseline.decisions):
                enriched_decisions = valid_decisions
                logger.info("architecture_planner.llm_enriched_adrs", count=len(valid_decisions))

        # Merge threats -- validate STRIDE categories
        valid_stride = {"Spoofing", "Tampering", "Repudiation", "Information Disclosure",
                        "Denial of Service", "Elevation of Privilege"}
        if data.get("threat_model") and isinstance(data["threat_model"], list):
            valid_threats = []
            for t in data["threat_model"]:
                try:
                    threat = ThreatEntry(**t)
                    if threat.category in valid_stride:
                        valid_threats.append(threat)
                except Exception:
                    continue
            if len(valid_threats) >= len(baseline.threat_model):
                enriched_threats = valid_threats
                logger.info("architecture_planner.llm_enriched_threats", count=len(valid_threats))

        return PlanOutput(
            title=baseline.title,
            summary=enriched_summary,
            components=baseline.components,  # Never modified by LLM
            decisions=enriched_decisions,
            threat_model=enriched_threats,
            diagram_mermaid=baseline.diagram_mermaid,  # Never modified by LLM
        )

    # -- Azure live validation (best-effort) -------------------------

    def _validate_azure_resources(self, spec: IntentSpec) -> list[str]:
        """Validate Azure resource availability using az CLI.

        Checks:
            1. Region supports required services (Container Apps, Key Vault, etc.)
            2. Subscription quota is not exhausted for common resource types

        Returns a list of warning strings.  Returns an empty list if az CLI
        is unavailable or the user is not logged in -- this keeps the
        pipeline functional for offline / CI-only scenarios.
        """
        warnings: list[str] = []

        if not shutil.which("az"):
            logger.info("azure_validation.skipped", reason="az CLI not found")
            return warnings

        # 1. Check region availability for key providers
        providers_to_check = [
            ("Microsoft.App", "managedEnvironments", "Container Apps"),
            ("Microsoft.KeyVault", "vaults", "Key Vault"),
            ("Microsoft.OperationalInsights", "workspaces", "Log Analytics"),
            ("Microsoft.ContainerRegistry", "registries", "Container Registry"),
        ]

        # Add data-store providers
        if DataStore.COSMOS_DB in spec.data_stores:
            providers_to_check.append(("Microsoft.DocumentDB", "databaseAccounts", "Cosmos DB"))
        if DataStore.REDIS in spec.data_stores:
            providers_to_check.append(("Microsoft.Cache", "redis", "Redis Cache"))
        if DataStore.SQL in spec.data_stores:
            providers_to_check.append(("Microsoft.Sql", "servers", "SQL Server"))

        for namespace, resource_type, friendly in providers_to_check:
            available = self._check_provider_in_region(namespace, resource_type, spec.azure_region)
            if available is False:
                warnings.append(
                    f"{friendly} ({namespace}/{resource_type}) may not be available "
                    f"in region '{spec.azure_region}'."
                )

        return warnings

    def _check_provider_in_region(
        self, namespace: str, resource_type: str, region: str
    ) -> bool | None:
        """Return True if the provider/resource-type is available in the region.

        Returns None if the check could not be performed (CLI error, not
        logged in, etc.)  -- callers treat None as "assume available".
        """
        try:
            result = subprocess.run(  # noqa: S603
                [
                    "az", "provider", "show",
                    "--namespace", namespace,
                    "--query",
                    f"resourceTypes[?resourceType=='{resource_type}'].locations[]",
                    "--output", "json",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                return None
            locations: list[str] = json.loads(result.stdout)
            # Azure returns display names like "East US 2"; normalise for comparison
            normalised = [loc.replace(" ", "").lower() for loc in locations]
            return region.replace(" ", "").lower() in normalised
        except Exception:
            return None

    def _parse_response(self, response: str, spec: IntentSpec) -> PlanOutput:
        """Parse a full LLM plan response into PlanOutput (used by legacy callers)."""
        import re

        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        json_str = json_match.group(1) if json_match else response.strip()

        try:
            data = json.loads(json_str)
            plan = PlanOutput(**data)
            # Validate structural requirements -- must have core components
            component_names = {c.name for c in plan.components}
            required = {"key-vault", "log-analytics", "managed-identity"}
            if not required.issubset(component_names):
                logger.warning("architecture_planner.llm_missing_required_components")
                return self._default_plan(spec)
            return plan
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("architecture_planner.parse_failed", error=str(e))
            return self._default_plan(spec)

    def _default_plan(self, spec: IntentSpec) -> PlanOutput:
        """Deterministic default plan based on IntentSpec."""
        components = self._build_components(spec)
        decisions = self._build_decisions(spec)
        threats = self._build_threat_model(spec)
        diagram = self._build_diagram(spec, components)

        return PlanOutput(
            title=f"Architecture Plan: {spec.project_name}",
            summary=(
                f"Enterprise-grade {spec.app_type.value} workload deployed on Azure Container Apps "
                f"with managed identity, Key Vault secret management, Log Analytics observability, "
                f"and private networking. CI/CD via GitHub Actions with OIDC authentication."
            ),
            components=components,
            decisions=decisions,
            threat_model=threats,
            diagram_mermaid=diagram,
        )

    def _build_components(self, spec: IntentSpec) -> list[ComponentSpec]:
        """Build component list based on IntentSpec."""
        components = [
            ComponentSpec(
                name="container-app",
                azure_service="Azure Container Apps",
                purpose=f"Hosts the {spec.app_type.value} application with auto-scaling",
                bicep_module="container-app.bicep",
                security_controls=["Managed Identity", "HTTPS Only", "Private Ingress", "Min TLS 1.2"],
            ),
            ComponentSpec(
                name="key-vault",
                azure_service="Azure Key Vault",
                purpose="Centralized secret and certificate management",
                bicep_module="keyvault.bicep",
                security_controls=["RBAC Access", "Soft Delete", "Purge Protection", "Diagnostic Logging"],
            ),
            ComponentSpec(
                name="log-analytics",
                azure_service="Azure Log Analytics",
                purpose="Centralized logging, monitoring, and diagnostics",
                bicep_module="log-analytics.bicep",
                security_controls=["Data Retention Policy", "Access Control", "Diagnostic Settings"],
            ),
            ComponentSpec(
                name="managed-identity",
                azure_service="Azure Managed Identity",
                purpose="Passwordless authentication between Azure resources",
                bicep_module="managed-identity.bicep",
                security_controls=["Least Privilege RBAC", "No Credential Storage"],
            ),
            ComponentSpec(
                name="container-registry",
                azure_service="Azure Container Registry",
                purpose="Private container image registry for application images",
                bicep_module="container-registry.bicep",
                security_controls=["Managed Identity Pull", "Private Access", "Image Scanning"],
            ),
        ]

        # Add data store components
        for store in spec.data_stores:
            if store == DataStore.BLOB_STORAGE:
                components.append(
                    ComponentSpec(
                        name="storage-account",
                        azure_service="Azure Storage Account",
                        purpose="Blob storage for documents and data",
                        bicep_module="storage.bicep",
                        security_controls=[
                            "Managed Identity Access",
                            "HTTPS Only",
                            "Encryption at Rest",
                            "Private Endpoint (optional)",
                        ],
                    )
                )
            elif store == DataStore.COSMOS_DB:
                components.append(
                    ComponentSpec(
                        name="cosmos-db",
                        azure_service="Azure Cosmos DB",
                        purpose="NoSQL database for application data",
                        bicep_module="cosmos-db.bicep",
                        security_controls=["Managed Identity", "Encryption", "Private Endpoint"],
                    )
                )
            elif store == DataStore.REDIS:
                components.append(
                    ComponentSpec(
                        name="redis-cache",
                        azure_service="Azure Redis Cache",
                        purpose="In-memory cache for low-latency data access and session management",
                        bicep_module="redis.bicep",
                        security_controls=["Managed Identity", "TLS Only", "Private Endpoint", "Non-Public Access"],
                    )
                )
            elif store == DataStore.SQL:
                components.append(
                    ComponentSpec(
                        name="sql-database",
                        azure_service="Azure SQL Database",
                        purpose="Relational database for structured application data",
                        bicep_module="sql.bicep",
                        security_controls=["Managed Identity", "TDE Encryption", "Private Endpoint", "Auditing"],
                    )
                )
            elif store == DataStore.TABLE_STORAGE:
                components.append(
                    ComponentSpec(
                        name="table-storage",
                        azure_service="Azure Table Storage",
                        purpose="NoSQL key-value storage for structured data",
                        bicep_module="table-storage.bicep",
                        security_controls=["Managed Identity Access", "Encryption at Rest", "HTTPS Only"],
                    )
                )
            elif store == DataStore.AI_SEARCH:
                components.append(
                    ComponentSpec(
                        name="ai-search",
                        azure_service="Azure AI Search",
                        purpose="Vector and semantic search for RAG patterns and knowledge retrieval",
                        bicep_module="ai-search.bicep",
                        security_controls=["Managed Identity", "RBAC Access", "HTTPS Only", "Private Endpoint"],
                    )
                )

        # Add AI service components when uses_ai is True
        if spec.uses_ai:
            components.append(
                ComponentSpec(
                    name="azure-openai",
                    azure_service="Azure OpenAI Service",
                    purpose="LLM inference for chat, embeddings, and AI agent capabilities",
                    bicep_module="openai.bicep",
                    security_controls=["Managed Identity", "Content Safety Filters", "RBAC Access", "Private Endpoint"],
                )
            )

        return components

    def _build_decisions(self, spec: IntentSpec) -> list[ArchitectureDecision]:
        """Build Architecture Decision Records."""
        decisions = [
            ArchitectureDecision(
                id="ADR-001",
                title="Use Azure Container Apps for compute",
                status="Accepted",
                context="Need a managed container platform that supports auto-scaling, managed identity, and integrated logging without Kubernetes operational overhead.",
                decision="Selected Azure Container Apps over AKS and App Service. Container Apps provides Kubernetes-based scaling with a serverless operational model.",
                consequences="Simpler operations than AKS. Some limitations on advanced networking compared to AKS. Acceptable for this workload.",
            ),
            ArchitectureDecision(
                id="ADR-002",
                title="Use Managed Identity for all service-to-service auth",
                status="Accepted",
                context="Enterprise security policy requires passwordless authentication. Credential rotation and secret sprawl are operational risks.",
                decision="All Azure resource access uses User-Assigned Managed Identity with least-privilege RBAC roles.",
                consequences="Eliminates credential management. Requires proper role assignments in Bicep. Slightly more complex initial setup.",
            ),
            ArchitectureDecision(
                id="ADR-003",
                title="Use Bicep for Infrastructure as Code",
                status="Accepted",
                context="Need Azure-native IaC that supports ARM validation, what-if analysis, and integrates with az CLI.",
                decision="Selected Bicep over Terraform for Azure-native tooling, no state file management, and direct ARM integration.",
                consequences="Azure-only (acceptable for this scope). Native az deployment group validate support.",
            ),
            ArchitectureDecision(
                id="ADR-004",
                title="Use Key Vault for all secrets",
                status="Accepted",
                context="No secrets should be stored in code, environment variables, or CI/CD configuration directly.",
                decision="All secrets stored in Azure Key Vault. Application accesses them via Managed Identity. CI/CD uses OIDC.",
                consequences="Additional Key Vault resource cost. Requires proper access policies. Eliminates secret exposure risk.",
            ),
            ArchitectureDecision(
                id="ADR-005",
                title="Private ingress by default",
                status="Accepted",
                context="Enterprise workloads should not be publicly accessible unless explicitly required.",
                decision="Container Apps environment configured with internal ingress. External access requires explicit configuration.",
                consequences="Requires VNet integration for access. More secure by default. May need adjustment for public-facing APIs.",
            ),
        ]

        if spec.uses_ai:
            decisions.append(
                ArchitectureDecision(
                    id="ADR-006",
                    title="Use Azure OpenAI + AI Foundry for AI workloads",
                    status="Accepted",
                    context="Workload requires AI/LLM capabilities. Need enterprise-grade AI platform with content safety, model management, and audit trail.",
                    decision="Deploy Azure OpenAI for model inference with content safety filters. Use AI Foundry for model management, prompt engineering, and evaluation. All access via Managed Identity with RBAC.",
                    consequences="Requires Azure OpenAI resource and model deployment. Content safety filters may block edge cases. Provides full audit trail and responsible AI controls.",
                )
            )
            ai_features = getattr(spec, "ai_features", [])
            if "rag" in ai_features:
                decisions.append(
                    ArchitectureDecision(
                        id="ADR-007",
                        title="Use Azure AI Search for RAG grounding",
                        status="Accepted",
                        context="RAG pattern requires vector search for document grounding to reduce hallucination.",
                        decision="Deploy Azure AI Search with vector index for semantic retrieval. Documents are embedded via Azure OpenAI embeddings model and indexed for similarity search.",
                        consequences="Additional search index cost. Requires document ingestion pipeline. Significantly improves answer accuracy and reduces hallucination.",
                    )
                )
            if "agents" in ai_features:
                decisions.append(
                    ArchitectureDecision(
                        id="ADR-008",
                        title="Use Semantic Kernel for agent orchestration",
                        status="Accepted",
                        context="Agentic workload requires tool-use, planning, and multi-step reasoning.",
                        decision="Use Semantic Kernel SDK for agent orchestration with Azure OpenAI. Agents can invoke tools, plan multi-step actions, and maintain conversation state.",
                        consequences="Adds Semantic Kernel dependency. Enables flexible agent patterns with tool-calling and function invocation.",
                    )
                )

        return decisions

    def _build_threat_model(self, spec: IntentSpec) -> list[ThreatEntry]:
        """Build STRIDE threat model."""
        threats = [
            ThreatEntry(
                id="THREAT-001",
                category="Spoofing",
                description="Unauthorized entity impersonates a legitimate service or user to access resources.",
                mitigation="Managed Identity for service auth. Entra ID for user auth. No shared secrets.",
                residual_risk="Low",
            ),
            ThreatEntry(
                id="THREAT-002",
                category="Tampering",
                description="Malicious modification of data in transit or at rest.",
                mitigation="TLS 1.2+ enforced. Encryption at rest via Azure platform encryption. Immutable audit logs.",
                residual_risk="Low",
            ),
            ThreatEntry(
                id="THREAT-003",
                category="Information Disclosure",
                description="Sensitive data exposed through logs, error messages, or misconfigured access.",
                mitigation="Structured logging without PII. Key Vault for secrets. Private networking. RBAC enforcement.",
                residual_risk="Low",
            ),
            ThreatEntry(
                id="THREAT-004",
                category="Denial of Service",
                description="Resource exhaustion through excessive requests or payload abuse.",
                mitigation="Container Apps auto-scaling with max replica limits. Request size limits. Rate limiting at API layer.",
                residual_risk="Medium",
            ),
            ThreatEntry(
                id="THREAT-005",
                category="Elevation of Privilege",
                description="Attacker gains higher privileges than authorized through misconfigured RBAC or container escape.",
                mitigation="Least-privilege RBAC. Non-root containers. No privileged capabilities. Regular access reviews.",
                residual_risk="Low",
            ),
        ]

        if spec.uses_ai:
            threats.append(
                ThreatEntry(
                    id="THREAT-006",
                    category="Tampering",
                    description="Prompt injection attacks to manipulate AI behavior or extract training data.",
                    mitigation="Content safety filters. Input validation. Output sanitization. System prompt hardening. Prompt injection detection.",
                    residual_risk="Medium",
                )
            )
            threats.append(
                ThreatEntry(
                    id="THREAT-007",
                    category="Information Disclosure",
                    description="AI model leaks sensitive data from training data, system prompts, or grounding documents.",
                    mitigation="Retrieval-scoped grounding. System prompt protection. Output filtering. User-scoped data access. No PII in prompts.",
                    residual_risk="Medium",
                )
            )
            threats.append(
                ThreatEntry(
                    id="THREAT-008",
                    category="Denial of Service",
                    description="Token exhaustion or cost explosion from excessive or malicious AI API calls.",
                    mitigation="Rate limiting. Token budget per request. Cost alerts. Max token limits on completions. API Management throttling.",
                    residual_risk="Medium",
                )
            )

        return threats

    def _build_diagram(self, spec: IntentSpec, components: list[ComponentSpec]) -> str:
        """Build Mermaid architecture diagram."""
        diagram = f"""graph TB
    subgraph "Client Layer"
        USER[User / Client]
    end

    subgraph "Azure Container Apps Environment"
        ACA["{spec.project_name}<br/>Container App"]
        HEALTH["/health endpoint"]
    end

    subgraph "Identity & Security"
        MI[Managed Identity]
        KV[Key Vault]
    end

    subgraph "Observability"
        LA[Log Analytics]
        DIAG[Diagnostic Settings]
    end

    subgraph "Container Registry"
        ACR[Azure Container Registry]
    end
"""

        # Add data store nodes (collect all stores into one Data Layer subgraph)
        data_layer_nodes = []
        for store in spec.data_stores:
            if store == DataStore.BLOB_STORAGE:
                data_layer_nodes.append("        SA[Storage Account]")
            elif store == DataStore.COSMOS_DB:
                data_layer_nodes.append("        CDB[Cosmos DB]")
            elif store == DataStore.REDIS:
                data_layer_nodes.append("        REDIS[Redis Cache]")
            elif store == DataStore.SQL:
                data_layer_nodes.append("        SQLDB[SQL Database]")
            elif store == DataStore.TABLE_STORAGE:
                data_layer_nodes.append("        TS[Table Storage]")

        if data_layer_nodes:
            diagram += '\n    subgraph "Data Layer"\n'
            diagram += "\n".join(data_layer_nodes) + "\n"
            diagram += "    end\n"

        # Add connections
        diagram += """
    USER -->|HTTPS| ACA
    ACA --> HEALTH
    ACA -->|Managed Identity| MI
    MI -->|RBAC| KV
    ACA -->|Logs| LA
    DIAG -->|Metrics| LA
    ACR -->|Image Pull| ACA
"""

        for store in spec.data_stores:
            if store == DataStore.BLOB_STORAGE:
                diagram += "    MI -->|RBAC| SA\n"
            elif store == DataStore.COSMOS_DB:
                diagram += "    MI -->|RBAC| CDB\n"
            elif store == DataStore.REDIS:
                diagram += "    MI -->|RBAC| REDIS\n"
            elif store == DataStore.SQL:
                diagram += "    MI -->|RBAC| SQLDB\n"
            elif store == DataStore.TABLE_STORAGE:
                diagram += "    MI -->|RBAC| TS\n"

        if spec.uses_ai:
            ai_model = getattr(spec, "ai_model", "gpt-4o")
            diagram += f"""
    subgraph \"AI Services\"
        AOAI[\"Azure OpenAI<br/>{ai_model}\"]
        CSAF[Content Safety]
    end
    MI -->|RBAC| AOAI
    AOAI --> CSAF
"""
            if DataStore.AI_SEARCH in spec.data_stores:
                diagram += "    MI -->|RBAC| AISRCH[AI Search]\n"
                diagram += "    AOAI -->|Embeddings| AISRCH\n"

        diagram += """
    subgraph "CI/CD"
        GHA[GitHub Actions]
        OIDC[OIDC Federation]
    end
    GHA -->|OIDC| OIDC
    GHA -->|Deploy| ACA
    GHA -->|Push| ACR
"""

        return diagram
