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
from src.orchestrator.generators.compilation_gate import CompilationGate
from src.orchestrator.generators.protocol import (
    GeneratorContext,
    create_default_registry,
)
from src.orchestrator.generators.scaffold_plan import ScaffoldPlan
from src.orchestrator.generators.scaffold_validator import ScaffoldValidator
from src.orchestrator.generators.ui_model_compiler import UIModelCompiler
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

    def __init__(self, config: AppConfig, standards_path: Path | None = None) -> None:
        self.config = config
        # Load enterprise standards from explicit path or default standards.yaml
        resolved = standards_path or Path("standards.yaml")
        self.standards = EnterpriseStandardsConfig.load(resolved)

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

        # Build the LLM call function from config (None if no provider)
        llm_call = self._build_llm_call()

        # Build the ScaffoldPlan -- single source of truth for ALL generators
        scaffold_plan = ScaffoldPlan.create(
            spec=spec,
            plan=plan,
            governance=gov_report,
            waf_report=waf_report,
            llm_call=llm_call,
            standards=self.standards,
        )

        logger.info(
            "infrastructure_generator.scaffold_plan_built",
            domain=scaffold_plan.uniqueness.domain if scaffold_plan.uniqueness else "unknown",
            enrichment_score=f"{scaffold_plan.uniqueness.enrichment_score:.2f}" if scaffold_plan.uniqueness else "0.00",
        )

        # Build the context that every generator receives (with scaffold_plan attached)
        context = GeneratorContext(
            plan=plan,
            governance=gov_report,
            waf_report=waf_report,
            standards=self.standards,
            scaffold_plan=scaffold_plan,
        )

        # Create the registry pre-loaded with all built-in generators
        registry = create_default_registry(standards=self.standards)

        # Run all generators in priority order via the uniform protocol
        files = registry.run_all(spec, context)

        # Layer 1: UIModelCompiler -- deterministic UI pages derived from entities
        # This replaces LLM-dependent Dashboard generation with compilable-by-construction output
        if spec.entities:
            compiler = UIModelCompiler()
            compiled_pages = compiler.compile_all(spec)
            # Compiled pages override LLM-generated ones (guaranteed to parse)
            files.update(compiled_pages)
            logger.info("infrastructure_generator.ui_compiled", pages=len(compiled_pages))

        # Layer 2: CompilationGate -- validate every file before output
        gate = CompilationGate()
        files, gate_result = gate.validate_and_fix(files)
        if not gate_result.all_passed:
            logger.warning(
                "infrastructure_generator.compilation_gate",
                errors=len(gate_result.errors),
                fixed=gate_result.files_fixed,
                summary=gate_result.summary(),
            )
            # Add gate report to output docs
            error_lines = ["# Compilation Gate Report", "", gate_result.summary(), ""]
            for err in gate_result.errors:
                error_lines.append(f"- **{err.file_path}**: {err.error_type} — {err.message}")
            files["docs/compilation-gate-report.md"] = "\n".join(error_lines)

        # Layer 3: Post-generation structural validation
        validator = ScaffoldValidator()
        validation = validator.validate(spec, files)
        if validation.issues:
            files["docs/validation-report.md"] = validation.to_markdown()
            logger.info(
                "infrastructure_generator.validation",
                errors=validation.error_count,
                warnings=validation.warning_count,
            )

        logger.info("infrastructure_generator.complete", file_count=len(files))
        return files

    def _build_llm_call(self):
        """Build LLM call function from config, or None if unavailable."""
        try:
            if self.config.llm.provider in ("template-only", ""):
                return None
            from src.orchestrator.agent import AgentRuntime
            runtime = AgentRuntime(self.config)
            return runtime.run_sync
        except Exception as exc:
            logger.warning("infrastructure_generator.llm_unavailable", error=str(exc))
            return None
