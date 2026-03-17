"""Generators package -- produces output artifacts (Bicep, docs, CI/CD, app code).

Exports the Plugin Protocol system for uniform generator access:

- ``GeneratorProtocol`` -- structural interface every generator satisfies
- ``GeneratorContext`` -- bundles spec-adjacent data (plan, governance, etc.)
- ``GeneratorRegistry`` -- collects and runs generators in priority order
- ``GeneratorAdapter`` -- wraps legacy generators to the protocol interface
- ``create_default_registry()`` -- factory for a fully-loaded registry
"""

from src.orchestrator.generators.protocol import (
    GeneratorAdapter,
    GeneratorContext,
    GeneratorProtocol,
    GeneratorRegistry,
    create_default_registry,
)

__all__ = [
    "GeneratorAdapter",
    "GeneratorContext",
    "GeneratorProtocol",
    "GeneratorRegistry",
    "create_default_registry",
]
