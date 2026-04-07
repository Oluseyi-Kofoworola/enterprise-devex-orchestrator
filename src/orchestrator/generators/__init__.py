"""Generators package -- produces output artifacts (Bicep, docs, CI/CD, app code).

Exports the Plugin Protocol system for uniform generator access:

- ``GeneratorProtocol`` -- structural interface every generator satisfies
- ``GeneratorContext`` -- bundles spec-adjacent data (plan, governance, etc.)
- ``GeneratorRegistry`` -- collects and runs generators in priority order
- ``GeneratorAdapter`` -- wraps legacy generators to the protocol interface
- ``create_default_registry()`` -- factory for a fully-loaded registry
- ``DomainContext`` / ``build_domain_context`` -- semantic domain model
- ``DeploymentProfile`` / ``SKUSelector`` -- environment-aware sizing
- ``RouteManifest`` / ``RouteBuilder`` -- canonical route definitions
- ``ScaffoldValidator`` -- post-generation consistency checks
- ``LLMEnricher`` / ``create_enricher`` -- optional AI enrichment layer
"""

from src.orchestrator.generators.deployment_profile import (
    DeploymentProfile,
    SKUSelector,
)
from src.orchestrator.generators.domain_context import DomainContext, build_domain_context
from src.orchestrator.generators.llm_enricher import LLMEnricher, create_enricher
from src.orchestrator.generators.protocol import (
    GeneratorAdapter,
    GeneratorContext,
    GeneratorProtocol,
    GeneratorRegistry,
    create_default_registry,
)
from src.orchestrator.generators.route_manifest import RouteBuilder, RouteManifest
from src.orchestrator.generators.scaffold_validator import ScaffoldValidator

__all__ = [
    "DeploymentProfile",
    "DomainContext",
    "GeneratorAdapter",
    "GeneratorContext",
    "GeneratorProtocol",
    "GeneratorRegistry",
    "LLMEnricher",
    "RouteBuilder",
    "RouteManifest",
    "SKUSelector",
    "ScaffoldValidator",
    "build_domain_context",
    "create_default_registry",
    "create_enricher",
]
