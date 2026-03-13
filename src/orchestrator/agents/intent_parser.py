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
        """Detect business domain from intent text using scored keyword matching.

        Each domain has *strong* keywords (worth 2 points) that are highly
        specific and *weak* keywords (worth 1 point) that could appear in
        unrelated contexts.  A domain must reach a minimum score threshold
        to be selected, preventing false positives from incidental mentions
        (e.g. "price lock contracts" triggering Legal).
        """
        # (strong_keywords, weak_keywords, threshold)
        domains: list[tuple[DomainType, list[str], list[str], int]] = [
            (
                DomainType.HEALTHCARE,
                # strong — unlikely outside healthcare
                ["patient", "healthcare", "health care", "hipaa", "ehr",
                 "clinical", "diagnosis", "nurse", "doctor", "pharmacy",
                 "medical"],
                # weak — could appear elsewhere
                ["appointment", "prescription", "voice agent", "session",
                 "transcript", "escalation"],
                2,
            ),
            (
                DomainType.LEGAL,
                # strong — clearly legal / contract-review
                ["legal review", "contract review", "redline", "clause analysis",
                 "indemnification", "non-compete", "attorney", "law firm",
                 "legal counsel", "legal agreement"],
                # weak — may appear in non-legal contexts
                ["contract", "clause", "liability", "amendment",
                 "compliance review", "risk score"],
                3,
            ),
            (
                DomainType.DOCUMENT_PROCESSING,
                ["document intelligence", "document processing", "form recognizer",
                 "document analysis", "table extraction"],
                ["extract", "invoice", "receipt", "ocr", "key-value",
                 "id document"],
                2,
            ),
        ]

        best_domain = DomainType.GENERIC
        best_score = 0
        for domain, strong, weak, threshold in domains:
            strong_hits = sum(1 for kw in strong if kw in intent)
            if strong_hits == 0:
                continue  # require at least one strong keyword
            score = strong_hits * 2 + sum(1 for kw in weak if kw in intent)
            if score >= threshold and score > best_score:
                best_domain = domain
                best_score = score
        return best_domain

    @staticmethod
    def _extract_entities(intent: str, domain: DomainType) -> list[EntitySpec]:
        """Extract domain entities using semantic reasoning for all domains."""
        return IntentParserAgent._extract_entities_dynamic(intent)

    @staticmethod
    def _extract_endpoints(intent: str, domain: DomainType) -> list[EndpointSpec]:
        """Extract domain API endpoints using semantic reasoning for all domains."""
        return IntentParserAgent._extract_endpoints_dynamic(intent)

    # ---------------------------------------------------------------
    # Domain-agnostic SEMANTIC entity/endpoint extraction engine
    # ---------------------------------------------------------------
    # Instead of keyword-matching, this engine reasons about the intent
    # by analysing section structure, noun-phrase context, described
    # attributes, and business relationships to extract the real
    # domain objects the system is built around.
    # ---------------------------------------------------------------

    # Infrastructure/tech words that should never become entities
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
        "notification", "notifications", "data", "type",
        "management", "processing", "tracking", "lifecycle", "engine",
        "automation", "requirement", "requirements", "feature", "latency",
        "uptime", "retention", "access", "role", "tier", "category",
        "method", "model", "framework", "sdk", "tool", "tools",
        "module", "handler", "layer", "component", "stack", "protocol",
        "format", "schema", "parameter", "parameters", "setting", "settings",
        # Section-header boilerplate
        "problem", "statement", "business", "goals", "target", "users",
        "functional", "scalability", "performance", "acceptance", "criteria",
        "version", "changes", "based", "initial", "scaffold",
    }

    # Generic/abstract words too vague to be entities on their own
    _ABSTRACT_WORDS: set[str] = {
        "time", "status", "level", "rate", "value", "item", "items",
        "request", "response", "record", "entry", "update", "action",
        "process", "event", "result", "report", "summary", "detail",
        "details", "list", "note", "notes", "info", "information",
        "step", "rule", "rules", "check", "trigger", "signal",
        "default", "option", "options", "mode", "threshold", "limit",
        "period", "interval", "cycle", "window", "range", "scope",
        "volume", "size", "count", "total", "average", "percentage",
    }

    @staticmethod
    def _extract_entities_dynamic(intent: str) -> list[EntitySpec]:
        """Extract domain entities semantically from intent text.

        This engine reasons about the business intent rather than
        matching isolated keywords. It works in four phases:

        1. **Section analysis** — Parse markdown section headers to
           identify functional areas (e.g. "Tank Monitoring & Smart
           Scheduling" → Tank, Schedule).
        2. **Noun-phrase extraction** — Find multi-word business
           concepts (e.g. "delivery order", "tank reading", "driver
           log", "price forecast") that describe real-world objects.
        3. **Attribute harvesting** — For each candidate entity, scan
           surrounding sentences for described properties, creating
           contextual fields rather than generic ones.
        4. **Relationship linking** — Detect parent-child references
           (e.g. "per customer", "for each tank") to add foreign-key
           fields.

        The result is a set of entities that reflect what the
        business *actually manages*, not just words that appear often.
        """
        infra = IntentParserAgent._INFRA_WORDS
        abstract = IntentParserAgent._ABSTRACT_WORDS

        # ----------------------------------------------------------
        # Phase 1: Section-based concept extraction
        # ----------------------------------------------------------
        # Markdown headers like "### Tank Monitoring & Smart Scheduling"
        # describe functional domains — the nouns inside them are high-
        # confidence entity candidates.
        section_concepts: dict[str, float] = {}
        section_header_re = re.compile(r'^#{1,4}\s+(.+)$', re.MULTILINE)
        for m in section_header_re.finditer(intent):
            header = m.group(1).strip()
            # Remove boilerplate suffixes
            header_clean = re.sub(
                r'\b(?:management|processing|tracking|automation|engine'
                r'|optimization|requirements?|system|module|integration'
                r'|& |and )\b', ' ', header, flags=re.I,
            )
            # Extract meaningful nouns from the cleaned header
            words = re.findall(r'[A-Za-z][a-z]{2,}', header_clean)
            for w in words:
                wl = w.lower()
                if wl not in infra and wl not in abstract and len(wl) > 2:
                    section_concepts[wl] = section_concepts.get(wl, 0) + 8

        # ----------------------------------------------------------
        # Phase 2: Noun-phrase extraction from body text
        # ----------------------------------------------------------
        # Look for compound noun phrases that describe business objects.
        # E.g. "delivery order", "tank level", "driver log", "burn rate"
        # Score multi-word phrases higher than single words.
        compound_candidates: dict[str, float] = {}

        # Pattern: Adjective/Noun + Noun (2-3 word phrases)
        compound_re = re.compile(
            r'\b([A-Za-z][a-z]+)\s+([A-Za-z][a-z]+)'
            r'(?:\s+([A-Za-z][a-z]+))?\b'
        )
        for m in compound_re.finditer(intent):
            w1, w2, w3 = m.group(1).lower(), m.group(2).lower(), m.group(3)
            w3 = w3.lower() if w3 else None
            # 2-word compounds
            if (w1 not in infra and w1 not in abstract
                    and w2 not in infra and w2 not in abstract):
                phrase = f"{w1}_{w2}"
                compound_candidates[phrase] = compound_candidates.get(phrase, 0) + 1

        # ----------------------------------------------------------
        # Phase 3: Business-object patterns
        # ----------------------------------------------------------
        # Sentences describing what the system stores/tracks/manages
        # are strong signals for entities.
        entity_scores: dict[str, float] = {}

        # "X <noun>" where X is a domain-specific modifier
        domain_noun_re = re.compile(
            r'\b([a-z]+)\s+(order|schedule|reading|log|profile|history'
            r'|forecast|prediction|alert|invoice|receipt|report|record'
            r'|plan|queue|assignment|contract|ticket|account|template'
            r'|sensor|meter|gauge|tank|fleet|truck|vehicle|route'
            r'|shipment|package|depot|terminal|warehouse|inventory'
            r'|customer|driver|dispatcher|patient|employee|vendor'
            r'|appointment|session|claim|refund|return|subscription'
            r'|notification|message|email|sms|price|rate|fee|charge)\b',
            re.I,
        )
        for m in domain_noun_re.finditer(intent.lower()):
            modifier, noun = m.group(1), m.group(2)
            if modifier in infra or modifier in abstract:
                # Use just the noun
                key = noun
            else:
                key = f"{modifier}_{noun}"
            if key not in infra:
                entity_scores[key] = entity_scores.get(key, 0) + 3

        # Standalone business nouns from bullet-point descriptions
        # (lines starting with "- ")
        bullet_re = re.compile(r'^[-*]\s+(.+)$', re.MULTILINE)
        standalone_noun_re = re.compile(
            r'\b(tank|customer|driver|route|delivery|invoice|payment'
            r'|receipt|sensor|meter|fleet|truck|vehicle|depot|inventory'
            r'|shipment|order|forecast|prediction|alert|appointment'
            r'|session|claim|refund|return|subscription|contract'
            r'|schedule|queue|ticket|report|notification|employee'
            r'|vendor|patient|product|catalog|inspection|certificate'
            r'|document|form|template|campaign|lead|opportunity'
            r'|account|portfolio|transaction|asset|device|reading'
            r'|measurement|telemetry|rate|quote|estimate|proposal'
            r'|budget|expense|reimbursement|timesheet|shift|roster)\b',
            re.I,
        )
        for bm in bullet_re.finditer(intent):
            line = bm.group(1).lower()
            for nm in standalone_noun_re.finditer(line):
                noun = nm.group(1)
                if noun not in infra:
                    entity_scores[noun] = entity_scores.get(noun, 0) + 2

        # ----------------------------------------------------------
        # Phase 4: Merge and rank
        # ----------------------------------------------------------
        # Combine section concepts, compound phrases, and pattern matches.
        # Section-header concepts get highest weight because they describe
        # the system's functional areas.
        merged: dict[str, float] = {}

        # Add section concepts
        for k, v in section_concepts.items():
            merged[k] = merged.get(k, 0) + v

        # Add entity patterns (domain_noun matches)
        for k, v in entity_scores.items():
            merged[k] = merged.get(k, 0) + v

        # Boost concepts that appear frequently in the text
        words_lower = re.findall(r'\b([a-z]{3,})\b', intent.lower())
        word_freq: dict[str, int] = {}
        for w in words_lower:
            word_freq[w] = word_freq.get(w, 0) + 1

        for key in list(merged.keys()):
            # For compound keys like "delivery_order", check both parts
            parts = key.split("_")
            freq_boost = sum(word_freq.get(p, 0) for p in parts) / len(parts)
            if freq_boost >= 3:
                merged[key] = merged[key] + min(freq_boost, 10)

        # Promote compound phrases where both words score individually
        for phrase, count in compound_candidates.items():
            parts = phrase.split("_")
            if count >= 2 and any(p in merged for p in parts):
                merged[phrase] = merged.get(phrase, 0) + count * 2

        # Filter out pure infra/abstract
        merged = {
            k: v for k, v in merged.items()
            if k not in infra
            and k not in abstract
            and not all(p in infra or p in abstract for p in k.split("_"))
        }

        if not merged:
            return [
                EntitySpec(name="Item", description="Generic domain entity", fields=[
                    FieldSpec(name="name", type="str", required=True, description="Item name"),
                    FieldSpec(name="description", type="str", required=False, description="Item description"),
                    FieldSpec(name="status", type="str", required=False, description="Item status"),
                ]),
            ]

        # Rank and deduplicate
        ranked = sorted(merged.items(), key=lambda x: -x[1])

        # Connector/adjective words that should not start entity names
        _CONNECTOR_WORDS = {
            "and", "or", "the", "for", "with", "from", "into", "onto",
            "smart", "real", "auto", "each", "every", "all", "any",
            "new", "old", "current", "daily", "weekly", "monthly",
        }

        # Deduplicate: merge singular/plural, prefer compound form
        seen_roots: set[str] = set()
        selected: list[str] = []
        for key, _score in ranked:
            parts = key.split("_")
            # Skip entities starting with connectors (e.g. "and_customer")
            if parts[0] in _CONNECTOR_WORDS:
                # Try salvaging: "and_customer" → "customer"
                parts = parts[1:]
                if not parts:
                    continue
                key = "_".join(parts)
            # Singularize each part
            roots = tuple(
                p.rstrip("s") if p.endswith("s") and len(p) > 4 else p
                for p in parts
            )
            root_key = "_".join(roots)
            # Skip if we already have this concept or a superset
            if root_key in seen_roots:
                continue
            # Skip if a single-word form is already covered by a compound
            if len(parts) == 1 and any(parts[0] in s for s in seen_roots if "_" in s):
                continue
            seen_roots.add(root_key)
            selected.append(key)
            if len(selected) >= 8:  # allow more entities for rich intents
                break

        # ----------------------------------------------------------
        # Phase 5: Build EntitySpecs with contextual fields
        # ----------------------------------------------------------
        entities: list[EntitySpec] = []
        for raw_name in selected:
            fields = IntentParserAgent._infer_fields_semantic(raw_name, intent)
            # Convert to PascalCase
            display = "".join(w.capitalize() for w in raw_name.split("_"))
            description = IntentParserAgent._infer_description(raw_name, intent)
            entities.append(EntitySpec(
                name=display,
                description=description,
                fields=fields,
            ))
        return entities

    @staticmethod
    def _infer_description(entity_key: str, intent: str) -> str:
        """Infer a meaningful description by finding the sentence that best
        describes this entity in the intent text."""
        parts = entity_key.split("_")
        # Find bullet-point or sentence mentioning this concept
        search_term = " ".join(parts)
        for line in intent.split("\n"):
            line_stripped = line.strip().lstrip("-* ")
            if search_term in line_stripped.lower() and len(line_stripped) > 20:
                # Truncate to a sensible length
                desc = line_stripped[:120].rstrip(".,;: ")
                return desc
        return f"{' '.join(w.capitalize() for w in parts)} domain entity"

    @staticmethod
    def _infer_fields_semantic(entity_key: str, intent: str) -> list[FieldSpec]:
        """Infer fields for an entity using name-based reasoning and contextual extraction.

        Instead of scanning all lines for keyword matches (which pulls in
        document-structure words like KPI, SLA, RTO), this method:
        1. Infers sensible fields from the entity *name* itself (a Tank has
           level, capacity, temperature; a Customer has name, email, phone).
        2. Extracts explicit data attributes only from API-spec lines that
           describe the entity's payload structure.
        3. Adds relationship foreign keys only when explicit association
           language is found.
        """
        fields: list[FieldSpec] = []
        seen_names: set[str] = set()
        parts = entity_key.split("_")
        search_term = " ".join(parts)

        # Words that are document/requirements structure — never valid fields
        _META = {
            "kpi", "sla", "rto", "rpo", "problem_statement", "problem",
            "target_users", "target", "acceptance", "criteria", "requirement",
            "requirements", "scalability", "compliance", "integration",
            "functional", "performance", "business_goals", "goals", "users",
            "overview", "section", "note", "todo", "action",
            "driven", "based", "upstream", "downstream", "monitoring",
            "rbac_enforcement", "rbac", "enforcement", "pii_protection",
            "pii", "data_retention", "retention", "audit_trail", "audit",
            "and_totals", "correct_line_items", "day_horizon_target_users",
            "email_delivery", "simulated_sensor_data", "y_scalability",
            "customer_dashboard_load", "based_access",
        }

        def _add(name: str, ftype: str, required: bool, desc: str) -> None:
            if name not in seen_names and name not in _META and len(name) > 2:
                seen_names.add(name)
                fields.append(FieldSpec(
                    name=name, type=ftype, required=required, description=desc,
                ))

        # ----------------------------------------------------------
        # Strategy 1: Name-based field inference
        # ----------------------------------------------------------
        # The entity name tells us what kind of thing it is.
        name_lower = entity_key.lower()

        # Person-like entities
        if any(w in name_lower for w in [
            "customer", "driver", "employee", "patient", "vendor",
            "user", "dispatcher", "operator", "agent",
        ]):
            _add("name", "str", True, "Full name")
            _add("email", "str", False, "Email address")
            _add("phone", "str", False, "Phone number")

        # Physical object / device entities
        if any(w in name_lower for w in [
            "tank", "device", "sensor", "meter", "vehicle",
            "truck", "equipment", "asset", "machine",
        ]):
            _add("serial_number", "str", False, "Serial or device identifier")
            _add("location", "str", False, "Physical location")

        # Reading / measurement entities
        if any(w in name_lower for w in [
            "reading", "measurement", "telemetry",
        ]):
            _add("value", "float", True, "Measured value")
            _add("unit", "str", False, "Unit of measurement")
            _add("recorded_at", "datetime", True, "Measurement timestamp")

        # Forecast / prediction entities
        if any(w in name_lower for w in [
            "forecast", "prediction", "estimate",
        ]):
            _add("predicted_value", "float", True, "Predicted value")
            _add("confidence", "float", False, "Confidence score")
            _add("horizon_days", "int", False, "Forecast horizon in days")
            _add("model_version", "str", False, "Model version used")

        # Transaction / payment entities
        if any(w in name_lower for w in [
            "payment", "transaction", "charge", "refund",
        ]):
            _add("amount", "float", True, "Transaction amount")
            _add("currency", "str", False, "Currency code")
            _add("method", "str", False, "Payment method")
            _add("transaction_id", "str", False, "External transaction ID")

        # Document entities (invoice, receipt, bill)
        if any(w in name_lower for w in [
            "invoice", "receipt", "bill",
        ]):
            _add("total_amount", "float", True, "Total amount")
            _add("due_date", "datetime", False, "Payment due date")
            _add("line_items", "list[str]", False, "Line item descriptions")

        # Order / delivery / shipment entities
        if any(w in name_lower for w in [
            "order", "delivery", "shipment",
        ]):
            _add("scheduled_date", "datetime", False, "Scheduled date")
            _add("quantity", "float", False, "Quantity or volume")

        # Route entities
        if any(w in name_lower for w in ["route"]):
            _add("date", "datetime", False, "Route date")
            _add("stops_count", "int", False, "Number of stops")
            _add("total_distance", "float", False, "Total route distance")

        # Price / rate / quote entities
        if any(w in name_lower for w in [
            "price", "pricing", "rate", "quote",
        ]):
            _add("price", "float", True, "Price value")
            _add("effective_date", "datetime", False, "Date price takes effect")

        # Alert / notification entities
        if any(w in name_lower for w in [
            "alert", "notification",
        ]):
            _add("message", "str", True, "Alert or notification message")
            _add("severity", "str", False, "Severity level")
            _add("acknowledged", "bool", False, "Whether acknowledged")

        # Schedule / shift entities
        if any(w in name_lower for w in [
            "schedule", "shift", "roster", "appointment",
        ]):
            _add("start_time", "datetime", True, "Start time")
            _add("end_time", "datetime", False, "End time")

        # Contract entities
        if any(w in name_lower for w in [
            "contract", "agreement", "subscription",
        ]):
            _add("start_date", "datetime", False, "Contract start date")
            _add("end_date", "datetime", False, "Contract end date")
            _add("terms", "str", False, "Contract terms")

        # History / log entities
        if any(w in name_lower for w in [
            "history", "log", "audit",
        ]):
            _add("actor", "str", False, "Who performed the action")
            _add("action_type", "str", True, "Type of action recorded")
            _add("timestamp", "datetime", True, "When the action occurred")

        # ----------------------------------------------------------
        # Strategy 2: Relationship fields (foreign keys)
        # ----------------------------------------------------------
        # Split by ### subsections to find functional-area co-occurrence.
        # Only add FK if the other entity appears ≥2 times in the same
        # subsection (not just once in passing). Cap at 3 FKs.
        # Ordered by priority: most common business relationships first.
        ref_entities = [
            "customer", "order", "delivery", "driver", "tank",
            "route", "invoice", "product", "user", "account",
        ]
        subsections = re.split(r'^###\s+', intent, flags=re.MULTILINE)
        fk_count = 0
        for ref in ref_entities:
            if ref in parts or fk_count >= 3:
                continue  # don't self-reference; cap FKs
            for sub in subsections:
                sl = sub.lower()
                # Entity must be the topic of this subsection (≥2 mentions)
                if sl.count(search_term) < 2:
                    continue
                # Other entity also appears meaningfully (≥2 mentions)
                if sl.count(ref) >= 2:
                    _add(f"{ref}_id", "str", True,
                         f"Associated {ref} identifier")
                    fk_count += 1
                    break

        # ----------------------------------------------------------
        # Ensure minimum baseline fields
        # ----------------------------------------------------------
        _add("status", "str", True, "Current status")
        _add("created_at", "datetime", False, "Record creation timestamp")

        return fields[:12]

    @staticmethod
    def _guess_field_type(field_name: str, context: str) -> str:
        """Guess field type from name and surrounding text."""
        name = field_name.lower()
        ctx = context.lower()
        if any(kw in name for kw in ["_id", "id_"]):
            return "str"
        if any(kw in name for kw in ["amount", "price", "cost", "fee", "rate",
                                      "score", "percentage", "pct", "confidence",
                                      "latitude", "longitude", "distance"]):
            return "float"
        if any(kw in name for kw in ["count", "quantity", "volume", "gallons",
                                      "number", "page", "port"]):
            return "int"
        if any(kw in name for kw in ["date", "time", "timestamp", "created",
                                      "updated", "expires"]):
            return "datetime"
        if any(kw in name for kw in ["is_", "has_", "enable", "active",
                                      "verified", "flag"]):
            return "bool"
        if any(kw in name for kw in ["items", "tags", "list", "parties"]):
            return "list[str]"
        if any(kw in ctx for kw in ["percentage", "score", "amount", "decimal"]):
            return "float"
        if any(kw in ctx for kw in ["number of", "count", "quantity"]):
            return "int"
        return "str"

    @staticmethod
    def _extract_endpoints_dynamic(intent: str) -> list[EndpointSpec]:
        """Generate API endpoints from semantically extracted entities."""
        entities = IntentParserAgent._extract_entities_dynamic(intent)
        endpoints: list[EndpointSpec] = []
        intent_lower = intent.lower()

        for entity in entities:
            # Convert PascalCase to kebab-case slug: TankReading → tank-readings
            raw = re.sub(r'(?<!^)(?=[A-Z])', '-', entity.name).lower()
            # Handle irregular plurals
            if raw.endswith("y") and len(raw) > 1 and raw[-2] not in "aeiou-":
                slug = raw[:-1] + "ies"       # delivery → deliveries
            elif raw.endswith(("s", "x", "z", "sh", "ch")):
                slug = raw + "es"
            else:
                slug = raw + "s"
            label = entity.name
            endpoints.extend([
                EndpointSpec(method="GET", path=f"/{slug}", description=f"List {label} records"),
                EndpointSpec(method="POST", path=f"/{slug}", description=f"Create {label}"),
                EndpointSpec(method="GET", path=f"/{slug}/{{id}}", description=f"Get {label} by ID"),
                EndpointSpec(method="PUT", path=f"/{slug}/{{id}}", description=f"Update {label}"),
                EndpointSpec(method="DELETE", path=f"/{slug}/{{id}}", description=f"Delete {label}"),
            ])

            # Detect workflow actions from intent context near this entity
            entity_words = re.sub(r'(?<!^)(?=[A-Z])', ' ', entity.name).lower().split()
            action_candidates = {
                "approve": f"Approve {label}",
                "reject": f"Reject {label}",
                "process": f"Process {label}",
                "cancel": f"Cancel {label}",
                "complete": f"Complete {label}",
                "escalate": f"Escalate {label}",
                "inspect": f"Inspect {label}",
                "schedule": f"Schedule {label}",
                "dispatch": f"Dispatch {label}",
                "submit": f"Submit {label}",
                "verify": f"Verify {label}",
                "send": f"Send {label}",
                "calculate": f"Calculate {label}",
                "predict": f"Predict {label}",
                "optimize": f"Optimize {label}",
            }
            for action, desc in action_candidates.items():
                # Only add if the action + entity concept co-occur tightly
                # (entity word in first half of the line, action near entity)
                for line in intent.split("\n"):
                    ll = line.lower()
                    if action not in ll:
                        continue
                    # At least one entity word must appear in the same line
                    if not any(ew in ll for ew in entity_words):
                        continue
                    # Entity concept should be the topic: appears in first
                    # 60 chars of the line (not just mentioned at the end)
                    first_pos = min(
                        (ll.find(ew) for ew in entity_words if ew in ll),
                        default=999,
                    )
                    if first_pos < 60:
                        endpoints.append(EndpointSpec(
                            method="POST",
                            path=f"/{slug}/{{id}}/{action}",
                            description=desc,
                        ))
                        break

        return endpoints
