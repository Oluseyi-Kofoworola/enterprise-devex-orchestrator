"""Infrastructure Generator Agent.

Takes an IntentSpec and PlanOutput and produces a complete, deployable
infrastructure scaffold including:
    - Bicep modules for all Azure resources (CAF naming + enterprise tags)
    - GitHub Actions CI/CD workflows
    - Application code scaffold
    - Documentation (including naming & tagging standards)

This is the final production agent in the chain after governance approval.

Uses the GeneratorRegistry / GeneratorProtocol to iterate over all
registered generators with a uniform interface, rather than hard-coding
each generator's bespoke signature.
"""

from __future__ import annotations

from pathlib import Path

from src.orchestrator.config import AppConfig
from src.orchestrator.generators.protocol import (
    GeneratorContext,
    create_default_registry,
)
from src.orchestrator.intent_schema import IntentSpec, PlanOutput
from src.orchestrator.logging import get_logger
from src.orchestrator.standards.config import EnterpriseStandardsConfig

logger = get_logger(__name__)


class InfrastructureGeneratorAgent:
    """Generates complete infrastructure scaffold from plan.

    This agent uses a ``GeneratorRegistry`` to dispatch work to all
    registered generators via the ``GeneratorProtocol`` interface.
    Enterprise standards (naming, tagging, governance) are applied via
    ``EnterpriseStandardsConfig``.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        # Load enterprise standards from standards.yaml if available
        standards_path = Path("standards.yaml")
        self.standards = EnterpriseStandardsConfig.load(standards_path)

    def generate(
        self,
        spec: IntentSpec,
        plan: PlanOutput,
        gov_report: object | None = None,
        waf_report: object | None = None,
    ) -> dict[str, str]:
        """Generate all scaffold files.

        Args:
            spec: The validated intent specification.
            plan: The approved architecture plan.
            gov_report: Optional governance report.
            waf_report: Optional WAF alignment report.

        Returns:
            Dictionary mapping file paths (relative) to file contents.
        """
        logger.info("infrastructure_generator.start", project=spec.project_name)

        # Build the context that every generator receives
        context = GeneratorContext(
            plan=plan,
            governance=gov_report,
            waf_report=waf_report,
            standards=self.standards,
        )

        # Create the registry pre-loaded with all built-in generators
        registry = create_default_registry(standards=self.standards)

        # Run all generators in priority order via the uniform protocol
        files = registry.run_all(spec, context)

        logger.info("infrastructure_generator.complete", file_count=len(files))
        return files
