"""Intent Parser Agent.

Takes raw natural-language business intent and normalizes it into a strict
IntentSpec schema. This is the first agent in the chain.

Responsibilities:
    - Extract project name, description, app type, data stores
    - Identify security requirements (compliance, auth, networking)
    - Determine observability and CI/CD needs
    - Record assumptions and confidence level
"""

from __future__ import annotations

import json
import re

from src.orchestrator.agent import AgentRuntime
from src.orchestrator.config import AppConfig
from src.orchestrator.intent_schema import (
    LANGUAGE_FRAMEWORKS,
    AppType,
    AuthModel,
    CICDRequirements,
    ComplianceFramework,
    ComputeTarget,
    DataStore,
    DomainType,
    EndpointSpec,
    EntitySpec,
    FieldSpec,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    SecurityRequirements,
)
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)

INTENT_PARSER_SYSTEM_PROMPT = """\
You are an Enterprise Intent Parser. Your job is to take a natural-language
business requirement and produce a strict JSON object conforming to the
IntentSpec schema.

## Rules
1. Extract a kebab-case project name from the description (3-39 chars, lowercase, alphanumeric + hyphens).
2. Identify the application type: api, web, worker, or function.
3. Determine data stores needed: blob_storage, cosmos_db, sql, table_storage, or none.
4. Assess security requirements:
   - Auth model: managed_identity (default), entra_id, api_key
   - Compliance: general (default), hipaa_guidance, soc2_guidance, fedramp_guidance
   - Networking: private (default), internal, public_restricted
   - Data classification: confidential (default), internal, public
5. Always enable: encryption_at_rest, encryption_in_transit, secret_management, log_analytics, diagnostic_settings, health_endpoint.
6. Record assumptions you made in the 'assumptions' array.
7. Set confidence between 0.0 and 1.0.
8. If the intent mentions AI/ML, set uses_ai to true.

## Output Format
Return ONLY a JSON object matching the IntentSpec schema. No markdown, no explanation.

## IntentSpec Schema Fields
{
  "project_name": "string (kebab-case)",
  "description": "string (max 200 chars)",
  "raw_intent": "string (original input)",
  "app_type": "api|web|worker|function",
  "language": "python",
  "framework": "fastapi",
  "data_stores": ["blob_storage"],
  "uses_ai": false,
  "security": {
    "auth_model": "managed_identity",
    "compliance_framework": "general",
    "networking": "private",
    "data_classification": "confidential",
    "encryption_at_rest": true,
    "encryption_in_transit": true,
    "secret_management": true,
    "enable_waf": false
  },
  "observability": {
    "log_analytics": true,
    "diagnostic_settings": true,
    "health_endpoint": true,
    "alerts": false,
    "dashboard": false
  },
  "cicd": {
    "validate_on_pr": true,
    "deploy_on_merge": false,
    "manual_deploy": true,
    "oidc_auth": true,
    "artifact_upload": true
  },
  "azure_region": "eastus2",
  "environment": "dev",
  "assumptions": [],
  "decisions": [],
  "open_risks": [],
  "confidence": 0.85
}
"""


class IntentParserAgent:
    """Parses raw business intent into a strict IntentSpec."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.runtime = AgentRuntime(config)

    def parse(self, raw_intent: str) -> IntentSpec:
        """Parse natural-language intent into IntentSpec.

        Uses the Copilot SDK agent to extract structured data. Falls back
        to rule-based parsing if the API is unavailable.
        """
        logger.info("intent_parser.start", intent_length=len(raw_intent))

        try:
            response = self.runtime.run_sync(
                system_prompt=INTENT_PARSER_SYSTEM_PROMPT,
                user_message=raw_intent,
                max_iterations=3,
            )
            spec = self._parse_response(response, raw_intent)
        except Exception as e:
            logger.debug("intent_parser.llm_fallback", error=str(e))
            spec = self._rule_based_parse(raw_intent)

        logger.info(
            "intent_parser.complete",
            project=spec.project_name,
            app_type=spec.app_type.value,
            confidence=spec.confidence,
        )
        return spec

    def _parse_response(self, response: str, raw_intent: str) -> IntentSpec:
        """Parse the LLM response into an IntentSpec."""
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to parse the entire response as JSON
            json_str = response.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("intent_parser.json_parse_failed")
            return self._rule_based_parse(raw_intent)

        # Ensure raw_intent is preserved
        data["raw_intent"] = raw_intent

        return IntentSpec(**data)

    def _rule_based_parse(self, raw_intent: str) -> IntentSpec:
        """Deterministic rule-based fallback parser.

        Extracts key signals from the intent text using pattern matching.
        Ensures the system always produces valid output, even without LLM.
        """
        logger.info("intent_parser.rule_based")
        intent_lower = raw_intent.lower()

        # Extract project name
        project_name = self._extract_project_name(intent_lower)

        # Detect app type
        app_type = self._detect_app_type(intent_lower)

        # Detect data stores
        data_stores = self._detect_data_stores(intent_lower)

        # Detect compliance
        compliance = self._detect_compliance(intent_lower)

        # Detect AI usage
        uses_ai = any(kw in intent_lower for kw in ["ai ", "ml ", "machine learning", "model", "llm", "gpt", "openai"])

        # Detect programming language
        language = self._detect_language(intent_lower)
        framework = LANGUAGE_FRAMEWORKS.get(language, "fastapi")

        # Detect compute target
        compute_target = self._detect_compute_target(intent_lower)

        # Detect networking
        networking = NetworkingModel.PRIVATE
        if any(kw in intent_lower for kw in ["public endpoint", "public-facing", "public access", "publicly accessible"]):
            networking = NetworkingModel.PUBLIC_RESTRICTED
        elif "internal" in intent_lower:
            networking = NetworkingModel.INTERNAL

        # Detect WAF
        enable_waf = any(kw in intent_lower for kw in [
            "waf", "web application firewall", "firewall",
        ])

        # Detect observability features from intent
        enable_alerts = any(kw in intent_lower for kw in [
            "alert", "alerts", "alerting", "monitoring", "notify", "notification",
            "proactive", "on-call",
        ])
        enable_dashboard = any(kw in intent_lower for kw in [
            "dashboard", "monitoring dashboard", "visibility", "real-time view",
            "observability dashboard",
        ])

        # Detect CI/CD preferences
        deploy_on_merge = any(kw in intent_lower for kw in [
            "deploy on merge", "auto-deploy", "autodeploy", "automatic deployment",
            "continuous deployment", "cd pipeline", "gitops",
        ])

        # Detect domain type
        domain_type = self._detect_domain(intent_lower)

        # Extract entities and endpoints for the detected domain
        entities = self._extract_entities(intent_lower, domain_type)
        endpoints = self._extract_endpoints(intent_lower, domain_type)

        return IntentSpec(
            project_name=project_name,
            description=raw_intent[:200],
            raw_intent=raw_intent,
            app_type=app_type,
            language=language,
            framework=framework,
            compute_target=compute_target,
            data_stores=data_stores,
            uses_ai=uses_ai,
            domain_type=domain_type,
            entities=entities,
            endpoints=endpoints,
            functional_summary=raw_intent[:500],
            security=SecurityRequirements(
                auth_model=AuthModel.MANAGED_IDENTITY,
                compliance_framework=compliance,
                networking=networking,
                enable_waf=enable_waf,
            ),
            observability=ObservabilityRequirements(
                alerts=enable_alerts,
                dashboard=enable_dashboard,
            ),
            cicd=CICDRequirements(
                deploy_on_merge=deploy_on_merge,
            ),
            azure_region=self.config.azure.location,
            assumptions=[
                f"Using {language.capitalize()} + {framework} as application stack",
                f"Azure {compute_target.value.replace('_', ' ').title()} as compute target",
                "Managed Identity for authentication",
                "Key Vault for secret management",
                "Log Analytics for observability",
            ],
            decisions=[
                f"Selected {compute_target.value.replace('_', ' ').title()} based on intent signals",
                "Private networking by default for security posture",
                "Bicep for infrastructure as code (Azure-native)",
            ],
            open_risks=[
                "Intent may require clarification for complex architectures",
            ],
            confidence=0.75,
        )

    @staticmethod
    def _extract_project_name(intent: str) -> str:
        """Extract a kebab-case project name from intent text."""
        # Try to find "build a <name>" or "create a <name>"
        match = re.search(
            r"(?:build|create|deploy|make)\s+(?:a\s+)?(\w[\w\s-]{2,30}?)(?:\s+(?:that|which|with|for|to))", intent
        )
        if match:
            name = match.group(1).strip()
            name = re.sub(r"[^a-z0-9\s-]", "", name.lower())
            name = re.sub(r"\s+", "-", name.strip())
            name = name[:39]
            if re.match(r"^[a-z][a-z0-9-]{2,38}$", name):
                return name

        # Fallback: generate from first meaningful words
        words = re.findall(r"[a-z]+", intent)
        meaningful = [
            w
            for w in words
            if w
            not in {
                "a",
                "an",
                "the",
                "that",
                "which",
                "with",
                "for",
                "to",
                "and",
                "or",
                "build",
                "create",
                "deploy",
                "make",
                "please",
                "i",
                "want",
                "need",
            }
        ]
        name = "-".join(meaningful[:4])
        if len(name) < 3:
            name = "enterprise-workload"
        return name[:39]

    @staticmethod
    def _detect_app_type(intent: str) -> AppType:
        """Detect application type from intent text using word-boundary matching."""

        def _has_word(keyword: str) -> bool:
            return bool(re.search(rf"\b{re.escape(keyword)}\b", intent))

        if any(_has_word(kw) for kw in ["api", "rest", "endpoint", "microservice"]):
            return AppType.API
        if any(_has_word(kw) for kw in ["web", "frontend", "ui", "dashboard"]):
            return AppType.WEB
        if any(_has_word(kw) for kw in ["worker", "background", "queue", "batch", "process"]):
            return AppType.WORKER
        if any(_has_word(kw) for kw in ["function", "serverless", "trigger", "event-driven"]):
            return AppType.FUNCTION
        return AppType.API

    @staticmethod
    def _detect_data_stores(intent: str) -> list[DataStore]:
        """Detect required data stores from intent text."""
        stores: list[DataStore] = []
        if any(kw in intent for kw in ["blob", "file", "document", "upload", "storage"]):
            stores.append(DataStore.BLOB_STORAGE)
        if any(kw in intent for kw in ["cosmos", "nosql", "json store"]):
            stores.append(DataStore.COSMOS_DB)
        if any(kw in intent for kw in ["sql", "database", "relational", "postgres"]):
            stores.append(DataStore.SQL)
        if any(kw in intent for kw in ["redis", "cache", "session"]):
            stores.append(DataStore.REDIS)
        if not stores:
            stores.append(DataStore.BLOB_STORAGE)
        return stores

    @staticmethod
    def _detect_compliance(intent: str) -> ComplianceFramework:
        """Detect compliance framework from intent text."""
        if "hipaa" in intent:
            return ComplianceFramework.HIPAA_GUIDANCE
        if "soc2" in intent or "soc 2" in intent:
            return ComplianceFramework.SOC2_GUIDANCE
        if "fedramp" in intent:
            return ComplianceFramework.FEDRAMP_GUIDANCE
        return ComplianceFramework.GENERAL

    @staticmethod
    def _detect_language(intent: str) -> str:
        """Detect programming language from intent text."""

        def _has(keyword: str) -> bool:
            return bool(re.search(rf"\b{re.escape(keyword)}\b", intent))

        if any(_has(kw) for kw in ["node", "nodejs", "javascript", "typescript", "express"]):
            return "node"
        if any(_has(kw) for kw in ["dotnet", ".net", "csharp", "c#", "aspnet", "asp.net"]):
            return "dotnet"
        return "python"

    @staticmethod
    def _detect_compute_target(intent: str) -> ComputeTarget:
        """Detect Azure compute target from intent text."""

        def _has(keyword: str) -> bool:
            return bool(re.search(rf"\b{re.escape(keyword)}\b", intent))

        if any(_has(kw) for kw in ["app service", "webapp", "web app"]):
            return ComputeTarget.APP_SERVICE
        if any(_has(kw) for kw in ["function", "functions", "serverless", "consumption"]):
            return ComputeTarget.FUNCTIONS
        return ComputeTarget.CONTAINER_APPS

    @staticmethod
    def _detect_domain(intent: str) -> DomainType:
        """Detect business domain from intent text."""
        healthcare_kw = [
            "patient", "healthcare", "health care", "appointment", "prescription",
            "medical", "clinical", "hipaa", "ehr", "diagnosis", "voice agent",
            "session", "transcript", "escalation", "nurse", "doctor", "pharmacy",
        ]
        legal_kw = [
            "contract", "clause", "legal", "redline", "compliance review",
            "risk score", "indemnification", "liability", "amendment",
            "attorney", "law firm", "legal review", "non-compete",
        ]
        docproc_kw = [
            "document intelligence", "document processing", "extract", "invoice",
            "receipt", "ocr", "table extraction", "key-value", "form recognizer",
            "document analysis", "id document",
        ]
        if any(kw in intent for kw in healthcare_kw):
            return DomainType.HEALTHCARE
        if any(kw in intent for kw in legal_kw):
            return DomainType.LEGAL
        if any(kw in intent for kw in docproc_kw):
            return DomainType.DOCUMENT_PROCESSING
        return DomainType.GENERIC

    @staticmethod
    def _extract_entities(intent: str, domain: DomainType) -> list[EntitySpec]:
        """Extract domain entities based on detected domain."""
        if domain == DomainType.HEALTHCARE:
            return [
                EntitySpec(name="Session", description="Voice agent session with patient", fields=[
                    FieldSpec(name="patient_id", type="str", required=True, description="Patient identifier"),
                    FieldSpec(name="status", type="str", required=True, description="active, completed, escalated"),
                    FieldSpec(name="transcript", type="list[str]", required=False, description="Conversation transcript"),
                    FieldSpec(name="intent_detected", type="str", required=False, description="Detected patient intent"),
                ]),
                EntitySpec(name="Appointment", description="Scheduled medical appointment", fields=[
                    FieldSpec(name="patient_id", type="str", required=True, description="Patient identifier"),
                    FieldSpec(name="provider", type="str", required=True, description="Healthcare provider name"),
                    FieldSpec(name="date_time", type="datetime", required=True, description="Appointment date and time"),
                    FieldSpec(name="status", type="str", required=True, description="scheduled, confirmed, cancelled"),
                    FieldSpec(name="reason", type="str", required=False, description="Visit reason"),
                ]),
                EntitySpec(name="PrescriptionRefill", description="Prescription refill request", fields=[
                    FieldSpec(name="patient_id", type="str", required=True, description="Patient identifier"),
                    FieldSpec(name="medication", type="str", required=True, description="Medication name"),
                    FieldSpec(name="pharmacy", type="str", required=False, description="Preferred pharmacy"),
                    FieldSpec(name="status", type="str", required=True, description="pending, approved, denied"),
                ]),
                EntitySpec(name="AuditLog", description="HIPAA audit trail entry", fields=[
                    FieldSpec(name="user_id", type="str", required=True, description="Actor identifier"),
                    FieldSpec(name="action", type="str", required=True, description="Action performed"),
                    FieldSpec(name="resource_type", type="str", required=True, description="Resource accessed"),
                    FieldSpec(name="resource_id", type="str", required=True, description="Resource identifier"),
                    FieldSpec(name="phi_accessed", type="bool", required=True, description="Whether PHI was accessed"),
                ]),
            ]
        if domain == DomainType.LEGAL:
            return [
                EntitySpec(name="Contract", description="Legal contract document", fields=[
                    FieldSpec(name="title", type="str", required=True, description="Contract title"),
                    FieldSpec(name="parties", type="list[str]", required=True, description="Contracting parties"),
                    FieldSpec(name="status", type="str", required=True, description="uploaded, analyzing, analyzed, approved"),
                    FieldSpec(name="file_path", type="str", required=False, description="Source document path"),
                    FieldSpec(name="risk_score", type="float", required=False, description="Overall risk score 0-100"),
                ]),
                EntitySpec(name="Clause", description="Extracted contract clause", fields=[
                    FieldSpec(name="contract_id", type="str", required=True, description="Parent contract ID"),
                    FieldSpec(name="category", type="str", required=True, description="indemnification, liability, termination, etc."),
                    FieldSpec(name="text", type="str", required=True, description="Clause text"),
                    FieldSpec(name="risk_level", type="str", required=True, description="low, medium, high, critical"),
                    FieldSpec(name="recommendation", type="str", required=False, description="Suggested action"),
                ]),
                EntitySpec(name="RiskAssessment", description="Contract risk assessment report", fields=[
                    FieldSpec(name="contract_id", type="str", required=True, description="Assessed contract ID"),
                    FieldSpec(name="overall_score", type="float", required=True, description="Risk score 0-100"),
                    FieldSpec(name="categories", type="dict", required=False, description="Per-category risk scores"),
                    FieldSpec(name="summary", type="str", required=True, description="Executive summary"),
                ]),
            ]
        if domain == DomainType.DOCUMENT_PROCESSING:
            return [
                EntitySpec(name="AnalysisResult", description="Document analysis result", fields=[
                    FieldSpec(name="document_name", type="str", required=True, description="Source document name"),
                    FieldSpec(name="model_id", type="str", required=True, description="Analysis model used"),
                    FieldSpec(name="status", type="str", required=True, description="processing, completed, failed"),
                    FieldSpec(name="confidence", type="float", required=False, description="Overall confidence score"),
                    FieldSpec(name="page_count", type="int", required=False, description="Number of pages analyzed"),
                ]),
                EntitySpec(name="ExtractedTable", description="Table extracted from document", fields=[
                    FieldSpec(name="analysis_id", type="str", required=True, description="Parent analysis ID"),
                    FieldSpec(name="page_number", type="int", required=True, description="Source page number"),
                    FieldSpec(name="rows", type="list", required=True, description="Table row data"),
                    FieldSpec(name="column_headers", type="list[str]", required=False, description="Column headers"),
                ]),
                EntitySpec(name="KeyValuePair", description="Extracted key-value pair", fields=[
                    FieldSpec(name="analysis_id", type="str", required=True, description="Parent analysis ID"),
                    FieldSpec(name="key", type="str", required=True, description="Extracted key"),
                    FieldSpec(name="value", type="str", required=True, description="Extracted value"),
                    FieldSpec(name="confidence", type="float", required=False, description="Extraction confidence"),
                ]),
            ]
        # Domain-agnostic: extract entities dynamically from intent text
        return IntentParserAgent._extract_entities_dynamic(intent)

    @staticmethod
    def _extract_endpoints(intent: str, domain: DomainType) -> list[EndpointSpec]:
        """Extract domain API endpoints based on detected domain."""
        if domain == DomainType.HEALTHCARE:
            return [
                EndpointSpec(method="POST", path="/sessions", description="Start new voice session"),
                EndpointSpec(method="GET", path="/sessions", description="List active sessions"),
                EndpointSpec(method="GET", path="/sessions/{id}", description="Get session details"),
                EndpointSpec(method="POST", path="/sessions/{id}/end", description="End a session"),
                EndpointSpec(method="POST", path="/sessions/{id}/escalate", description="Escalate to human agent"),
                EndpointSpec(method="GET", path="/appointments", description="List appointments"),
                EndpointSpec(method="POST", path="/appointments", description="Book appointment"),
                EndpointSpec(method="DELETE", path="/appointments/{id}", description="Cancel appointment"),
                EndpointSpec(method="GET", path="/prescriptions", description="List prescription refills"),
                EndpointSpec(method="POST", path="/prescriptions", description="Request prescription refill"),
                EndpointSpec(method="GET", path="/audit-logs", description="Query audit trail"),
            ]
        if domain == DomainType.LEGAL:
            return [
                EndpointSpec(method="POST", path="/contracts/upload", description="Upload contract document"),
                EndpointSpec(method="GET", path="/contracts", description="List contracts"),
                EndpointSpec(method="GET", path="/contracts/{id}", description="Get contract details"),
                EndpointSpec(method="POST", path="/contracts/{id}/analyze", description="Start clause analysis"),
                EndpointSpec(method="GET", path="/contracts/{id}/clauses", description="Get extracted clauses"),
                EndpointSpec(method="GET", path="/contracts/{id}/risk-report", description="Get risk assessment"),
                EndpointSpec(method="POST", path="/contracts/{id}/redlines", description="Generate redlines"),
            ]
        if domain == DomainType.DOCUMENT_PROCESSING:
            return [
                EndpointSpec(method="POST", path="/analyze", description="Submit document for analysis"),
                EndpointSpec(method="GET", path="/analyses", description="List analysis results"),
                EndpointSpec(method="GET", path="/analyses/{id}", description="Get analysis result"),
                EndpointSpec(method="GET", path="/analyses/{id}/tables", description="Get extracted tables"),
                EndpointSpec(method="GET", path="/analyses/{id}/key-values", description="Get key-value pairs"),
                EndpointSpec(method="GET", path="/models", description="List available analysis models"),
            ]
        return IntentParserAgent._extract_endpoints_dynamic(intent)

    # ---------------------------------------------------------------
    # Domain-agnostic entity/endpoint extraction engine
    # ---------------------------------------------------------------

    # Words to ignore when scanning for entity candidates
    _STOPWORDS: set[str] = {
        "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "at",
        "by", "with", "from", "as", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "shall", "should", "may", "might", "can", "could", "must", "that",
        "this", "these", "those", "it", "its", "our", "their", "your", "we",
        "they", "you", "all", "each", "every", "any", "both", "such", "not",
        "but", "if", "when", "than", "into", "about", "up", "out", "per",
    }

    # Infrastructure / tech words to filter out from entity candidates
    _INFRA_WORDS: set[str] = {
        "azure", "api", "apis", "database", "server", "cloud", "deploy",
        "docker", "kubernetes", "container", "containers", "endpoint",
        "endpoints", "service", "services", "system", "systems", "application",
        "applications", "platform", "infrastructure", "environment", "region",
        "cluster", "resource", "resources", "configuration", "config",
        "authentication", "authorization", "identity", "key", "vault",
        "monitor", "log", "logs", "logging", "storage", "blob", "cosmos",
        "redis", "sql", "http", "https", "rest", "json", "yaml", "bicep",
        "github", "cicd", "pipeline", "workflow", "terraform", "helm",
        "compliance", "security", "networking", "integration", "webhook",
        "notification", "notifications", "data", "time", "type", "status",
        "management", "processing", "tracking", "lifecycle", "engine",
        "automation", "requirement", "requirements", "feature", "latency",
        "uptime", "retention", "access", "role", "tier", "category",
        "method", "model", "framework", "sdk", "tool", "tools",
    }

    @staticmethod
    def _extract_entities_dynamic(intent: str) -> list[EntitySpec]:
        """Extract domain entities from intent text — fully domain-agnostic.

        Scans for noun phrases that represent business concepts, then infers
        fields for each entity based on context clues in the intent text.
        Works for any industry without hardcoded domain logic.
        """
        candidates: dict[str, int] = {}
        stop = IntentParserAgent._STOPWORDS
        infra = IntentParserAgent._INFRA_WORDS

        # Strategy 1: "X management/processing/tracking/engine" patterns
        compound_re = re.compile(
            r'\b(\w+)\s+(?:management|processing|tracking|lifecycle|engine'
            r'|automation|workflow|service|module|handler)\b', re.I
        )
        for m in compound_re.finditer(intent):
            word = m.group(1).lower()
            if word not in stop and word not in infra and len(word) > 2:
                candidates[word] = candidates.get(word, 0) + 5

        # Strategy 2: verb + noun patterns ("manage X", "track X", etc.)
        action_re = re.compile(
            r'\b(?:manage|track|process|automate|handle|create|submit|review'
            r'|approve|calculate|generate|validate|initiate|inspect)\s+'
            r'(?:the\s+)?(?:a\s+)?(\w+)', re.I
        )
        for m in action_re.finditer(intent):
            word = m.group(1).lower()
            if word not in stop and word not in infra and len(word) > 2:
                candidates[word] = candidates.get(word, 0) + 4

        # Strategy 3: "X API", "X endpoint", "X request" patterns
        api_re = re.compile(
            r'\b(\w+)\s+(?:api|endpoint|request|response|record|entry'
            r'|transaction|calculation|rule|check|report)\b', re.I
        )
        for m in api_re.finditer(intent):
            word = m.group(1).lower()
            if word not in stop and word not in infra and len(word) > 2:
                candidates[word] = candidates.get(word, 0) + 3

        # Strategy 4: frequency boost — domain nouns that appear often
        words = re.findall(r'\b([a-z]{3,})\b', intent.lower())
        for w in words:
            if w in candidates:
                candidates[w] += 1

        if not candidates:
            # Absolute fallback: generic Item
            return [
                EntitySpec(name="Item", description="Generic domain entity", fields=[
                    FieldSpec(name="name", type="str", required=True, description="Item name"),
                    FieldSpec(name="description", type="str", required=False, description="Item description"),
                    FieldSpec(name="status", type="str", required=False, description="Item status"),
                ]),
            ]

        # Rank and take top entities (max 5)
        ranked = sorted(candidates.items(), key=lambda x: -x[1])
        # Deduplicate singulars/plurals: prefer singular
        seen: set[str] = set()
        selected: list[str] = []
        for word, _score in ranked:
            singular = word.rstrip("s") if word.endswith("s") and len(word) > 4 else word
            if singular not in seen and word not in seen:
                seen.add(singular)
                seen.add(word)
                selected.append(singular)
            if len(selected) >= 5:
                break

        # Build EntitySpecs with context-inferred fields
        entities: list[EntitySpec] = []
        for noun in selected:
            fields = IntentParserAgent._infer_fields(noun, intent)
            name = noun[0].upper() + noun[1:]  # Capitalize
            entities.append(EntitySpec(
                name=name,
                description=f"{name} domain entity",
                fields=fields,
            ))
        return entities

    @staticmethod
    def _infer_fields(entity_name: str, intent: str) -> list[FieldSpec]:
        """Infer fields for an entity based on its name and the intent context."""
        fields: list[FieldSpec] = []
        intent_lower = intent.lower()

        # Financial entities: refund, payment, invoice, charge, fee, price, cost
        financial_kw = {"refund", "payment", "invoice", "charge", "fee", "price", "cost", "transaction"}
        if entity_name in financial_kw or any(kw in intent_lower for kw in [f"{entity_name} amount", f"{entity_name} calculation"]):
            fields.append(FieldSpec(name="amount", type="float", required=True, description="Monetary amount"))
            fields.append(FieldSpec(name="currency", type="str", required=False, description="Currency code (e.g. USD)"))
            fields.append(FieldSpec(name="method", type="str", required=False, description="Processing method"))

        # Process/request entities: return, request, claim, order, ticket, case
        process_kw = {"return", "request", "claim", "order", "ticket", "case", "application", "submission"}
        if entity_name in process_kw:
            fields.append(FieldSpec(name="reason", type="str", required=False, description="Reason or justification"))
            fields.append(FieldSpec(name="priority", type="str", required=False, description="Priority level"))

        # Check for reference fields from context
        ref_entities = {"customer", "user", "order", "product", "account", "patient", "employee", "vendor"}
        for ref in ref_entities:
            if ref != entity_name and ref in intent_lower:
                fields.append(FieldSpec(
                    name=f"{ref}_id", type="str", required=True,
                    description=f"Associated {ref} identifier",
                ))

        # If intent mentions items/products with this entity, add items field
        if entity_name in {"return", "order", "shipment", "cart"} and "item" in intent_lower:
            fields.append(FieldSpec(name="items", type="list[str]", required=False, description="Associated item IDs"))

        # Every entity gets a status and description
        if not any(f.name == "status" for f in fields):
            fields.append(FieldSpec(name="status", type="str", required=True, description="Current status"))
        fields.append(FieldSpec(name="notes", type="str", required=False, description="Additional notes"))

        return fields

    @staticmethod
    def _extract_endpoints_dynamic(intent: str) -> list[EndpointSpec]:
        """Generate API endpoints from dynamically extracted entities."""
        entities = IntentParserAgent._extract_entities_dynamic(intent)
        endpoints: list[EndpointSpec] = []
        intent_lower = intent.lower()

        for entity in entities:
            slug = entity.name.lower() + "s"  # pluralize
            label = entity.name
            endpoints.extend([
                EndpointSpec(method="GET", path=f"/{slug}", description=f"List {label} records"),
                EndpointSpec(method="POST", path=f"/{slug}", description=f"Create {label}"),
                EndpointSpec(method="GET", path=f"/{slug}/{{id}}", description=f"Get {label} by ID"),
                EndpointSpec(method="PUT", path=f"/{slug}/{{id}}", description=f"Update {label}"),
                EndpointSpec(method="DELETE", path=f"/{slug}/{{id}}", description=f"Delete {label}"),
            ])

            # Detect workflow actions from intent context
            word = entity.name.lower()
            action_map = {
                "approve": f"Approve {label}",
                "reject": f"Reject {label}",
                "process": f"Process {label}",
                "cancel": f"Cancel {label}",
                "complete": f"Complete {label}",
                "escalate": f"Escalate {label}",
                "inspect": f"Inspect {label}",
            }
            for action, desc in action_map.items():
                if re.search(rf'\b{action}\w*\b', intent_lower):
                    endpoints.append(EndpointSpec(
                        method="POST", path=f"/{slug}/{{id}}/{action}", description=desc,
                    ))

        return endpoints
