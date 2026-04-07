"""Generator Protocol -- enforces a uniform contract for all generators.

Every generator in the pipeline implements GeneratorProtocol, which defines a
single entry point: generate(spec, context) -> dict[str, str].  This replaces
the previous ad-hoc signatures (some took plan, some didn't, CostEstimator used
``estimate()``) with a consistent interface that the InfrastructureGeneratorAgent
can iterate over without hard-coding each generator's quirks.

The protocol uses Python's structural subtyping (typing.Protocol / runtime_checkable)
so generators do NOT need to inherit from a base class -- they just need to have
the right method signature.

**Adapter pattern:** Existing generators keep their original signatures untouched.
``GeneratorAdapter`` wraps any generator class and maps the uniform
``generate(spec, context)`` call to the class's native method, so zero production
code changes are needed in the generators themselves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

from src.orchestrator.intent_schema import IntentSpec, PipelineTier, PlanOutput
from src.orchestrator.logging import get_logger
from src.orchestrator.standards.config import EnterpriseStandardsConfig

logger = get_logger(__name__)

# Avoid circular imports -- these are only used for type annotations in
# GeneratorContext and the adapter logic, imported lazily where needed.
GovernanceReport = Any  # src.orchestrator.intent_schema.GovernanceReport
WAFAlignmentReport = Any  # src.orchestrator.standards.waf.WAFAlignmentReport

# Lazy import for ScaffoldPlan to avoid circular dependencies
ScaffoldPlanType = Any  # src.orchestrator.generators.scaffold_plan.ScaffoldPlan


@dataclass(frozen=True)
class GeneratorContext:
    """Bundles all optional context a generator might need.

    Generators that only need ``spec`` can ignore the context entirely.
    Those that need ``plan``, ``governance``, or ``waf_report`` pull from here.

    When a ``scaffold_plan`` is attached, generators can access:
        - ctx.scaffold_plan.uniqueness  -- UniquenessProfile
        - ctx.scaffold_plan.services    -- GenerationServices (enricher, domain, tokens)
    """

    plan: PlanOutput | None = None
    governance: GovernanceReport | None = None
    waf_report: WAFAlignmentReport | None = None
    version: int = 1
    standards: EnterpriseStandardsConfig | None = None
    extra: dict[str, object] = field(default_factory=dict)
    scaffold_plan: ScaffoldPlanType = None


@runtime_checkable
class GeneratorProtocol(Protocol):
    """Structural protocol that every generator must satisfy.

    Implementations must define ``generate(spec, context)`` returning a
    dict mapping relative file paths to file contents.  The protocol is
    ``runtime_checkable`` so callers can assert conformance with
    ``isinstance(gen, GeneratorProtocol)``.
    """

    def generate(self, spec: IntentSpec, context: GeneratorContext) -> dict[str, str]:
        """Produce output files for the given spec and optional context."""
        ...


# ---------------------------------------------------------------------------
# Adapter -- wraps existing generators without modifying them
# ---------------------------------------------------------------------------

class GeneratorAdapter:
    """Adapts a generator with any signature to the uniform GeneratorProtocol.

    Callers provide a *bridge* function that maps ``(inner, spec, context)`` to
    the generator's native method.  Pre-built bridges for every built-in
    generator are available via ``create_default_registry()``.
    """

    def __init__(
        self,
        inner: object,
        bridge: Callable[[object, IntentSpec, GeneratorContext], dict[str, str]],
    ) -> None:
        self._inner = inner
        self._bridge = bridge

    def generate(self, spec: IntentSpec, context: GeneratorContext) -> dict[str, str]:
        return self._bridge(self._inner, spec, context)


# -- Bridge functions for each built-in generator -------------------------

def _bridge_spec_only(gen: object, spec: IntentSpec, ctx: GeneratorContext) -> dict[str, str]:
    """Bridge for generators whose ``generate()`` takes only ``spec``.

    If the generator has a ``set_scaffold_plan()`` method, call it first
    to inject the platform-wide planning objects before generation.
    """
    if ctx.scaffold_plan is not None and hasattr(gen, "set_scaffold_plan"):
        gen.set_scaffold_plan(ctx.scaffold_plan)
    return gen.generate(spec)  # type: ignore[union-attr]


def _bridge_spec_plan(gen: object, spec: IntentSpec, ctx: GeneratorContext) -> dict[str, str]:
    """Bridge for BicepGenerator: ``generate(spec, plan)``."""
    if ctx.scaffold_plan is not None and hasattr(gen, "set_scaffold_plan"):
        gen.set_scaffold_plan(ctx.scaffold_plan)
    return gen.generate(spec, ctx.plan)  # type: ignore[union-attr]


def _bridge_cicd(gen: object, spec: IntentSpec, ctx: GeneratorContext) -> dict[str, str]:
    """Bridge for CICDGenerator: ``generate(spec, version=1)``."""
    if ctx.scaffold_plan is not None and hasattr(gen, "set_scaffold_plan"):
        gen.set_scaffold_plan(ctx.scaffold_plan)
    return gen.generate(spec, version=ctx.version)  # type: ignore[union-attr]


def _bridge_docs(gen: object, spec: IntentSpec, ctx: GeneratorContext) -> dict[str, str]:
    """Bridge for DocsGenerator: ``generate(spec, plan, governance, waf_report)``."""
    if ctx.scaffold_plan is not None and hasattr(gen, "set_scaffold_plan"):
        gen.set_scaffold_plan(ctx.scaffold_plan)
    return gen.generate(  # type: ignore[union-attr]
        spec, ctx.plan, governance=ctx.governance, waf_report=ctx.waf_report,
    )


def _bridge_cost(gen: object, spec: IntentSpec, ctx: GeneratorContext) -> dict[str, str]:
    """Bridge for CostEstimator: ``estimate(spec, plan)`` -> markdown file."""
    if ctx.scaffold_plan is not None and hasattr(gen, "set_scaffold_plan"):
        gen.set_scaffold_plan(ctx.scaffold_plan)
    estimate = gen.estimate(spec, ctx.plan)  # type: ignore[union-attr]
    return {"docs/cost-estimate.md": estimate.to_markdown()}


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------

@dataclass
class GeneratorRegistration:
    """Metadata for a registered generator."""

    name: str
    generator: GeneratorProtocol
    priority: int = 100  # lower = runs earlier
    min_tier: PipelineTier = PipelineTier.STANDARD  # minimum tier required to run


class GeneratorRegistry:
    """Registry that collects generators and runs them in priority order.

    Usage::

        registry = create_default_registry(standards=config)
        files = registry.run_all(spec, context)
    """

    def __init__(self) -> None:
        self._generators: list[GeneratorRegistration] = []

    def register(
        self,
        name: str,
        generator: GeneratorProtocol,
        priority: int = 100,
        min_tier: PipelineTier = PipelineTier.STANDARD,
    ) -> None:
        """Register a generator under *name* with the given *priority*."""
        self._generators.append(
            GeneratorRegistration(name=name, generator=generator, priority=priority, min_tier=min_tier)
        )

    def unregister(self, name: str) -> bool:
        """Remove a generator by name.  Returns True if found."""
        before = len(self._generators)
        self._generators = [g for g in self._generators if g.name != name]
        return len(self._generators) < before

    @property
    def names(self) -> list[str]:
        """Return registered generator names in priority order."""
        return [g.name for g in sorted(self._generators, key=lambda g: g.priority)]

    def get(self, name: str) -> GeneratorProtocol | None:
        """Return the generator registered under *name*, or None."""
        for g in self._generators:
            if g.name == name:
                return g.generator
        return None

    def run_all(
        self,
        spec: IntentSpec,
        context: GeneratorContext,
    ) -> dict[str, str]:
        """Execute generators in priority order, filtered by pipeline tier.

        Only generators whose ``min_tier`` satisfies the spec's ``pipeline_tier``
        are executed. Tier ordering: MICRO < STANDARD < ENTERPRISE.
        """
        tier_order = {PipelineTier.MICRO: 0, PipelineTier.STANDARD: 1, PipelineTier.ENTERPRISE: 2}
        current_tier = tier_order.get(spec.pipeline_tier, 1)

        files: dict[str, str] = {}
        for reg in sorted(self._generators, key=lambda g: g.priority):
            gen_tier = tier_order.get(reg.min_tier, 1)
            if gen_tier > current_tier:
                logger.info("generator.skipped_by_tier", name=reg.name, min_tier=reg.min_tier.value, current_tier=spec.pipeline_tier.value)
                continue
            result = reg.generator.generate(spec, context)
            files.update(result)
        return files

    def __len__(self) -> int:
        return len(self._generators)

    def __contains__(self, name: str) -> bool:
        return any(g.name == name for g in self._generators)


def create_default_registry(
    standards: EnterpriseStandardsConfig | None = None,
) -> GeneratorRegistry:
    """Build a registry pre-loaded with all built-in generators.

    This is the single place where generators are registered.  Adding a new
    generator only requires adding one import + one ``register()`` call here
    -- no changes to ``InfrastructureGeneratorAgent`` are needed.
    """
    from src.orchestrator.generators.alert_generator import AlertGenerator
    from src.orchestrator.generators.app_generator import AppGenerator
    from src.orchestrator.generators.bicep_generator import BicepGenerator
    from src.orchestrator.generators.cicd_generator import CICDGenerator
    from src.orchestrator.generators.cost_estimator import CostEstimator
    from src.orchestrator.generators.dashboard_generator import DashboardGenerator
    from src.orchestrator.generators.docs_generator import DocsGenerator
    from src.orchestrator.generators.fabric_generator import FabricGenerator
    from src.orchestrator.generators.frontend_api_generator import FrontendApiGenerator
    from src.orchestrator.generators.frontend_generator import FrontendGenerator
    from src.orchestrator.generators.test_generator import ScaffoldTestGenerator

    registry = GeneratorRegistry()

    # Priority order: infra first, then app code, then supporting artifacts
    # Tier: MICRO = minimal (API+Bicep+Docker), STANDARD = full, ENTERPRISE = full+extras
    registry.register("bicep", GeneratorAdapter(BicepGenerator(standards=standards), _bridge_spec_plan), priority=10, min_tier=PipelineTier.MICRO)
    registry.register("cicd", GeneratorAdapter(CICDGenerator(), _bridge_cicd), priority=20, min_tier=PipelineTier.MICRO)
    registry.register("app", GeneratorAdapter(AppGenerator(), _bridge_spec_only), priority=30, min_tier=PipelineTier.MICRO)
    registry.register("fabric", GeneratorAdapter(FabricGenerator(), _bridge_spec_only), priority=35, min_tier=PipelineTier.STANDARD)
    registry.register("frontend", GeneratorAdapter(FrontendGenerator(), _bridge_spec_only), priority=40, min_tier=PipelineTier.STANDARD)
    registry.register("frontend-api", GeneratorAdapter(FrontendApiGenerator(), _bridge_spec_only), priority=42, min_tier=PipelineTier.STANDARD)
    registry.register("docs", GeneratorAdapter(DocsGenerator(), _bridge_docs), priority=50, min_tier=PipelineTier.STANDARD)
    registry.register("tests", GeneratorAdapter(ScaffoldTestGenerator(), _bridge_spec_only), priority=60, min_tier=PipelineTier.MICRO)
    registry.register("alerts", GeneratorAdapter(AlertGenerator(), _bridge_spec_only), priority=70, min_tier=PipelineTier.ENTERPRISE)
    registry.register("dashboard", GeneratorAdapter(DashboardGenerator(), _bridge_spec_only), priority=80, min_tier=PipelineTier.ENTERPRISE)
    registry.register("cost", GeneratorAdapter(CostEstimator(), _bridge_cost), priority=90, min_tier=PipelineTier.ENTERPRISE)

    return registry
