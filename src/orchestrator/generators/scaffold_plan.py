"""Scaffold Plan -- unified planning objects for the dynamic generation pipeline.

This module defines the three core platform objects that replace the old
GeneratorContext and enable truly dynamic, LLM-enriched scaffold generation:

    ScaffoldPlan    -- master plan built ONCE, consumed by ALL generators
    UniquenessProfile   -- per-domain personality that makes each scaffold unique
    GenerationServices  -- shared services (enricher, cache, LLM bridge)

Design principles:
    1. ONE plan, ONE uniqueness model, ONE enrichment service
    2. All generators consume the same ScaffoldPlan -- no generator builds its own
    3. UniquenessProfile is deterministic (domain-derived) + optionally LLM-enriched
    4. GenerationServices wraps LLM access with guardrails and caching
    5. Fallback to deterministic defaults when LLM is unavailable
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from src.orchestrator.generators.design_system import DesignSystem, DesignTokens
from src.orchestrator.generators.domain_context import DomainContext, build_domain_context
from src.orchestrator.generators.llm_enricher import (
    EnrichmentGuardrail,
    EnrichmentResult,
    EnrichmentTarget,
    EnrichmentType,
    LLMEnricher,
    create_enricher,
)
from src.orchestrator.intent_schema import IntentSpec, PlanOutput
from src.orchestrator.logging import get_logger
from src.orchestrator.standards.config import EnterpriseStandardsConfig

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────────
# Uniqueness Profile
# ────────────────────────────────────────────────────────────────────

@dataclass
class UniquenessProfile:
    """Per-domain personality that makes each scaffold visually and semantically unique.

    Built deterministically from DesignSystem + DomainContext, and optionally
    enriched by LLM for richer descriptions and copy text.
    """

    # Identity
    domain: str = "generic"
    project_persona: str = ""  # e.g., "A mission-critical healthcare data platform"
    tagline: str = ""  # e.g., "Streamlining patient care through intelligent document processing"

    # Frontend personality
    dashboard_title: str = "Dashboard"
    dashboard_subtitle: str = ""
    kpi_definitions: list[dict[str, str]] = field(default_factory=list)
    # Each KPI: {"label": "...", "key": "...", "icon": "...", "color": "..."}
    empty_state_messages: dict[str, str] = field(default_factory=dict)
    # entity_name -> "No patients found. Start by adding a new patient record."
    action_labels: dict[str, dict[str, str]] = field(default_factory=dict)
    # entity_name -> {"create": "Register Patient", "delete": "Discharge Patient"}
    column_labels: dict[str, dict[str, str]] = field(default_factory=dict)
    # entity_name -> {"name": "Patient Name", "status": "Care Status"}
    page_titles: dict[str, str] = field(default_factory=dict)
    # entity_name -> "Patient Registry"

    # Backend personality
    api_descriptions: dict[str, str] = field(default_factory=dict)
    # entity_name -> "Manages patient lifecycle from admission to discharge"
    service_docstrings: dict[str, str] = field(default_factory=dict)
    # entity_name -> "Service handling patient CRUD operations and care coordination."
    error_messages: dict[str, dict[str, str]] = field(default_factory=dict)
    # entity_name -> {"not_found": "Patient record not found", "conflict": "Patient ID already exists"}

    # Documentation personality
    project_overview: str = ""
    architecture_narrative: str = ""
    deployment_intro: str = ""
    security_narrative: str = ""

    # Seed data personality
    seed_descriptions: dict[str, list[str]] = field(default_factory=dict)
    # entity_name -> ["A routine cardiac follow-up appointment scheduled for...", ...]

    # Design tokens (from DesignSystem)
    design_tokens: DesignTokens | None = None

    # Scoring
    enrichment_score: float = 0.0  # 0.0 = all deterministic, 1.0 = all LLM-enriched


def _build_deterministic_kpis(spec: IntentSpec, domain_ctx: DomainContext) -> list[dict[str, str]]:
    """Build domain-aware KPI definitions from entities and domain context."""
    kpis: list[dict[str, str]] = []
    entities = spec.entities

    # Primary count KPI -- always the first entity
    if entities:
        primary = entities[0]
        label = primary.name.replace("_", " ")
        kpis.append({
            "label": f"Total {label}s",
            "key": "total_primary",
            "icon": "database",
            "color": "primary",
        })

    # Status-based KPI -- if any entity has a status field
    for ent in entities:
        for f in ent.fields:
            if f.name.lower() in ("status", "state", "phase"):
                kpis.append({
                    "label": f"Active {ent.name.replace('_', ' ')}s",
                    "key": f"active_{ent.name.lower()}",
                    "icon": "activity",
                    "color": "success",
                })
                break
        if len(kpis) >= 2:
            break

    # Entity count KPI
    kpis.append({
        "label": "Entity Types",
        "key": "entity_types",
        "icon": "layers",
        "color": "info",
    })

    # Domain-specific KPIs
    domain_kpi_map = {
        "healthcare": {"label": "Critical Cases", "icon": "alert-triangle", "color": "danger"},
        "fintech": {"label": "Pending Transactions", "icon": "clock", "color": "warning"},
        "logistics": {"label": "In Transit", "icon": "truck", "color": "info"},
        "ecommerce": {"label": "Open Orders", "icon": "shopping-cart", "color": "accent"},
        "iot_smart_city": {"label": "Active Sensors", "icon": "radio", "color": "success"},
        "legal": {"label": "Contracts Under Review", "icon": "file-text", "color": "warning"},
        "education": {"label": "Active Enrollments", "icon": "users", "color": "info"},
        "manufacturing": {"label": "Production Lines", "icon": "settings", "color": "accent"},
        "cybersecurity": {"label": "Open Incidents", "icon": "shield", "color": "danger"},
    }
    domain_kpi = domain_kpi_map.get(domain_ctx.domain_type.value if hasattr(domain_ctx.domain_type, "value") else str(domain_ctx.domain_type))
    if domain_kpi:
        kpis.append({
            "label": domain_kpi["label"],
            "key": "domain_metric",
            "icon": domain_kpi["icon"],
            "color": domain_kpi["color"],
        })

    # Needs attention KPI
    kpis.append({
        "label": "Needs Attention",
        "key": "needs_attention",
        "icon": "alert-circle",
        "color": "warning",
    })

    return kpis


def _build_deterministic_labels(spec: IntentSpec, domain_ctx: DomainContext) -> dict:
    """Build deterministic entity-specific labels from entities and domain."""
    empty_states: dict[str, str] = {}
    action_labels: dict[str, dict[str, str]] = {}
    column_labels: dict[str, dict[str, str]] = {}
    page_titles: dict[str, str] = {}

    for ent in spec.entities:
        name = ent.name
        readable = name.replace("_", " ")
        lower = readable.lower()

        # Page titles
        page_titles[name] = f"{readable} Management"

        # Empty states
        empty_states[name] = f"No {lower} records found. Create your first {lower} to get started."

        # Action labels
        action_labels[name] = {
            "create": f"Add {readable}",
            "delete": f"Remove {readable}",
            "edit": f"Edit {readable}",
            "view": f"View {readable}",
        }

        # Column labels from fields
        cols: dict[str, str] = {}
        for f in ent.fields:
            # Convert field_name to "Field Name"
            cols[f.name] = f.name.replace("_", " ").title()
        column_labels[name] = cols

    return {
        "empty_states": empty_states,
        "action_labels": action_labels,
        "column_labels": column_labels,
        "page_titles": page_titles,
    }


def _build_deterministic_api_descriptions(spec: IntentSpec) -> dict[str, str]:
    """Build deterministic API descriptions for each entity."""
    descriptions: dict[str, str] = {}
    for ent in spec.entities:
        readable = ent.name.replace("_", " ")
        desc = ent.description if ent.description else f"Manages {readable.lower()} records and lifecycle operations."
        descriptions[ent.name] = desc
    return descriptions


def build_uniqueness_profile(
    spec: IntentSpec,
    domain_ctx: DomainContext,
    tokens: DesignTokens,
    enricher: LLMEnricher | None = None,
) -> UniquenessProfile:
    """Build a UniquenessProfile from deterministic sources + optional LLM enrichment.

    This is the single factory function. Called ONCE before generators run.
    """
    # ── Deterministic base ──
    domain = tokens.domain
    labels = _build_deterministic_labels(spec, domain_ctx)
    kpis = _build_deterministic_kpis(spec, domain_ctx)
    api_descs = _build_deterministic_api_descriptions(spec)

    brand = domain_ctx.ui_brand_label
    project_readable = spec.project_name.replace("-", " ").title()

    profile = UniquenessProfile(
        domain=domain,
        project_persona=f"{project_readable} — {brand}",
        tagline=spec.description or f"Enterprise {project_readable} platform",
        dashboard_title=f"{project_readable}",
        dashboard_subtitle=f"Operational overview for {brand}",
        kpi_definitions=kpis,
        empty_state_messages=labels["empty_states"],
        action_labels=labels["action_labels"],
        column_labels=labels["column_labels"],
        page_titles=labels["page_titles"],
        api_descriptions=api_descs,
        service_docstrings={
            ent.name: f"Service layer for {ent.name.replace('_', ' ').lower()} CRUD operations."
            for ent in spec.entities
        },
        error_messages={
            ent.name: {
                "not_found": f"{ent.name.replace('_', ' ')} record not found.",
                "conflict": f"A {ent.name.replace('_', ' ').lower()} with this identifier already exists.",
                "validation": f"Invalid {ent.name.replace('_', ' ').lower()} data provided.",
            }
            for ent in spec.entities
        },
        project_overview=spec.description or f"Enterprise-grade {project_readable} platform.",
        architecture_narrative=f"Cloud-native architecture for {project_readable} on Azure Container Apps.",
        deployment_intro=f"Deployment guide for {project_readable} to Azure.",
        security_narrative=f"Security controls and compliance posture for {project_readable}.",
        design_tokens=tokens,
    )

    # ── LLM enrichment (optional) ──
    if enricher and enricher.is_enabled:
        profile = _enrich_profile(profile, spec, domain_ctx, enricher)

    return profile


def _enrich_profile(
    profile: UniquenessProfile,
    spec: IntentSpec,
    domain_ctx: DomainContext,
    enricher: LLMEnricher,
) -> UniquenessProfile:
    """Enrich a UniquenessProfile using LLM for richer, domain-specific text."""
    enriched_count = 0
    total_targets = 0

    # ── Enrich project persona & tagline ──
    persona_target = EnrichmentTarget(
        target_type=EnrichmentType.ENTITY_DESCRIPTION,
        context=(
            f"Project: {spec.project_name}\n"
            f"Domain: {profile.domain}\n"
            f"Description: {spec.description}\n"
            f"Entities: {', '.join(e.name for e in spec.entities)}\n"
            "Write a compelling one-sentence project persona."
        ),
        default_value=profile.project_persona,
        max_length=200,
    )
    tagline_target = EnrichmentTarget(
        target_type=EnrichmentType.ENTITY_DESCRIPTION,
        context=(
            f"Project: {spec.project_name}\n"
            f"Domain: {profile.domain}\n"
            f"Description: {spec.description}\n"
            "Write a concise tagline (under 15 words) for this platform."
        ),
        default_value=profile.tagline,
        max_length=150,
    )
    total_targets += 2

    results = enricher.enrich_batch([persona_target, tagline_target])
    if results[0].was_enriched:
        profile.project_persona = results[0].enriched
        enriched_count += 1
    if results[1].was_enriched:
        profile.tagline = results[1].enriched
        enriched_count += 1

    # ── Enrich empty state messages ──
    for ent in spec.entities:
        target = EnrichmentTarget(
            target_type=EnrichmentType.SEED_DESCRIPTION,
            context=(
                f"Entity: {ent.name}\nDomain: {profile.domain}\n"
                f"Write a friendly empty-state message for when there are no {ent.name.replace('_', ' ').lower()} records. "
                "Include a call-to-action. One sentence only."
            ),
            default_value=profile.empty_state_messages.get(ent.name, "No records found."),
            max_length=200,
        )
        total_targets += 1
        result = enricher.enrich(target)
        if result.was_enriched:
            profile.empty_state_messages[ent.name] = result.enriched
            enriched_count += 1

    # ── Enrich API descriptions ──
    for ent in spec.entities:
        fields_str = ", ".join(f.name for f in ent.fields[:8])
        target = EnrichmentTarget(
            target_type=EnrichmentType.ENTITY_DESCRIPTION,
            context=(
                f"Entity: {ent.name}\nFields: {fields_str}\nDomain: {profile.domain}\n"
                f"Write a one-sentence API description for this entity's REST endpoint."
            ),
            default_value=profile.api_descriptions.get(ent.name, f"Manages {ent.name} records."),
            max_length=200,
        )
        total_targets += 1
        result = enricher.enrich(target)
        if result.was_enriched:
            profile.api_descriptions[ent.name] = result.enriched
            enriched_count += 1

    # ── Enrich documentation sections ──
    doc_targets = [
        ("project_overview", "Write a 2-sentence project overview."),
        ("architecture_narrative", "Write a 2-sentence architecture overview for this Azure cloud-native platform."),
        ("deployment_intro", "Write a 1-sentence deployment introduction."),
        ("security_narrative", "Write a 2-sentence security overview."),
    ]
    for attr, instruction in doc_targets:
        target = EnrichmentTarget(
            target_type=EnrichmentType.DOC_SECTION,
            context=(
                f"Project: {spec.project_name}\nDomain: {profile.domain}\n"
                f"Entities: {', '.join(e.name for e in spec.entities)}\n"
                f"{instruction}"
            ),
            default_value=getattr(profile, attr),
            max_length=400,
        )
        total_targets += 1
        result = enricher.enrich(target)
        if result.was_enriched:
            setattr(profile, attr, result.enriched)
            enriched_count += 1

    # ── Score ──
    profile.enrichment_score = enriched_count / max(total_targets, 1)
    logger.info(
        "uniqueness_profile.enriched",
        enriched=enriched_count,
        total=total_targets,
        score=f"{profile.enrichment_score:.2f}",
    )

    return profile


# ────────────────────────────────────────────────────────────────────
# Generation Services
# ────────────────────────────────────────────────────────────────────

class EnrichmentCache:
    """Simple in-memory cache for enrichment results to avoid duplicate LLM calls."""

    def __init__(self) -> None:
        self._cache: dict[str, EnrichmentResult] = {}

    def _key(self, target: EnrichmentTarget) -> str:
        raw = f"{target.target_type.value}:{target.context}:{target.max_length}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, target: EnrichmentTarget) -> EnrichmentResult | None:
        return self._cache.get(self._key(target))

    def put(self, target: EnrichmentTarget, result: EnrichmentResult) -> None:
        self._cache[self._key(target)] = result

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Not tracked in this simple implementation."""
        return 0.0


class CachedEnricher:
    """LLMEnricher wrapper that adds caching."""

    def __init__(self, enricher: LLMEnricher, cache: EnrichmentCache | None = None) -> None:
        self._enricher = enricher
        self._cache = cache or EnrichmentCache()

    @property
    def is_enabled(self) -> bool:
        return self._enricher.is_enabled

    def enrich(self, target: EnrichmentTarget) -> EnrichmentResult:
        cached = self._cache.get(target)
        if cached is not None:
            return cached
        result = self._enricher.enrich(target)
        self._cache.put(target, result)
        return result

    def enrich_batch(self, targets: list[EnrichmentTarget]) -> list[EnrichmentResult]:
        return [self.enrich(t) for t in targets]


@dataclass
class GenerationServices:
    """Shared services available to ALL generators during the pipeline.

    Created once by the orchestrator, passed into every generator.
    """

    enricher: CachedEnricher
    domain_ctx: DomainContext
    design_tokens: DesignTokens
    standards: EnterpriseStandardsConfig | None = None

    @staticmethod
    def create(
        spec: IntentSpec,
        llm_call: Callable[[str, str], str] | None = None,
        standards: EnterpriseStandardsConfig | None = None,
    ) -> GenerationServices:
        """Factory: build all shared services from an IntentSpec.

        This is the single entry point for creating services. Called once
        by the orchestrator before running generators.
        """
        domain_ctx = build_domain_context(spec)
        design_sys = DesignSystem()
        tokens = design_sys.generate_tokens(spec)
        enricher = CachedEnricher(create_enricher(llm_call))

        return GenerationServices(
            enricher=enricher,
            domain_ctx=domain_ctx,
            design_tokens=tokens,
            standards=standards,
        )


# ────────────────────────────────────────────────────────────────────
# Scaffold Plan
# ────────────────────────────────────────────────────────────────────

@dataclass
class ScaffoldPlan:
    """Master plan built ONCE, consumed by ALL generators.

    Replaces GeneratorContext as the single source of truth for the
    generation pipeline. Every generator receives the same ScaffoldPlan.
    """

    # Core inputs
    spec: IntentSpec
    plan: PlanOutput | None = None
    governance: Any = None  # GovernanceReport
    waf_report: Any = None  # WAFAlignmentReport
    version: int = 1

    # Shared services
    services: GenerationServices | None = None

    # Uniqueness profile
    uniqueness: UniquenessProfile | None = None

    # Legacy compatibility
    @property
    def standards(self) -> EnterpriseStandardsConfig | None:
        return self.services.standards if self.services else None

    @staticmethod
    def create(
        spec: IntentSpec,
        plan: PlanOutput | None = None,
        governance: Any = None,
        waf_report: Any = None,
        version: int = 1,
        llm_call: Callable[[str, str], str] | None = None,
        standards: EnterpriseStandardsConfig | None = None,
    ) -> ScaffoldPlan:
        """Build the complete ScaffoldPlan including services and uniqueness profile.

        This is the top-level factory. Called ONCE by InfrastructureGeneratorAgent.
        """
        services = GenerationServices.create(spec, llm_call=llm_call, standards=standards)

        profile = build_uniqueness_profile(
            spec=spec,
            domain_ctx=services.domain_ctx,
            tokens=services.design_tokens,
            enricher=services.enricher,
        )

        return ScaffoldPlan(
            spec=spec,
            plan=plan,
            governance=governance,
            waf_report=waf_report,
            version=version,
            services=services,
            uniqueness=profile,
        )
