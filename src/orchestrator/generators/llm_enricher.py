"""LLM Enrichment Layer -- optional AI-powered enhancement of generated output.

Provides constrained, guardrailed LLM enrichment for specific targets:
- Seed data descriptions (make them domain-specific and realistic)
- ADR rationale text (add architectural context)
- Documentation sections (improve readability)

Design principles:
1. All enrichment is OPTIONAL -- scaffold works 100% without it
2. Enrichment targets are constrained -- only specific text segments
3. Guardrails prevent structural changes -- LLM can only fill text slots
4. Fallback to deterministic defaults on any failure
5. LLM output is validated before use

Components:
- EnrichmentTarget: defines what can be enriched and constraints
- EnrichmentGuardrail: validates LLM output before acceptance
- LLMEnricher: orchestrates enrichment with the Copilot SDK
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


class EnrichmentType(str, Enum):
    """Types of content that can be enriched."""
    SEED_DESCRIPTION = "seed_description"
    ADR_RATIONALE = "adr_rationale"
    DOC_SECTION = "doc_section"
    ENTITY_DESCRIPTION = "entity_description"
    THREAT_MITIGATION = "threat_mitigation"
    # Phase 2 additions — platform-wide enrichment
    UI_COPY = "ui_copy"               # Empty states, action labels, page titles
    API_DOCSTRING = "api_docstring"    # Service/route docstrings
    ERROR_MESSAGE = "error_message"    # Domain-specific error messages
    SEED_VALUE = "seed_value"          # Individual mock data values
    REACT_COMPONENT = "react_component" # Dynamic React component generation


@dataclass(frozen=True)
class EnrichmentTarget:
    """Defines a single enrichment target with constraints."""
    target_type: EnrichmentType
    context: str  # Context to provide to the LLM
    default_value: str  # Fallback if enrichment fails
    max_length: int = 500  # Maximum output length
    must_contain: list[str] = field(default_factory=list)  # Required substrings
    must_not_contain: list[str] = field(default_factory=list)  # Forbidden patterns


@dataclass
class EnrichmentResult:
    """Result of an enrichment attempt."""
    original: str
    enriched: str
    was_enriched: bool
    target_type: EnrichmentType
    rejection_reason: str = ""


class EnrichmentGuardrail:
    """Validates LLM output against constraints before acceptance."""

    # Patterns that indicate the LLM generated code instead of text
    _CODE_PATTERNS = [
        r"```",
        r"def \w+\(",
        r"class \w+:",
        r"import \w+",
        r"from \w+ import",
        r"function \w+\(",
        r"const \w+ =",
        r"<script",
        r"<\?php",
    ]

    # Patterns that indicate prompt injection or instruction override
    _INJECTION_PATTERNS = [
        r"ignore (?:all )?(?:previous |prior )?instructions",
        r"you are now",
        r"new instructions:",
        r"system prompt",
        r"<\|.*?\|>",
    ]

    @staticmethod
    def validate(target: EnrichmentTarget, output: str) -> tuple[bool, str]:
        """Validate LLM output against target constraints.

        Returns:
            (is_valid, rejection_reason)
        """
        if not output or not output.strip():
            return False, "Empty output"

        # Length check
        if len(output) > target.max_length:
            return False, f"Output exceeds max length ({len(output)} > {target.max_length})"

        # Must-contain check
        for required in target.must_contain:
            if required.lower() not in output.lower():
                return False, f"Missing required content: '{required}'"

        # Must-not-contain check
        for forbidden in target.must_not_contain:
            if forbidden.lower() in output.lower():
                return False, f"Contains forbidden content: '{forbidden}'"

        # Code pattern check
        # Only apply code pattern check if we aren't expecting code
        if target.target_type != EnrichmentType.REACT_COMPONENT:
            for pattern in EnrichmentGuardrail._CODE_PATTERNS:
                if re.search(pattern, output):
                    return False, f"Output contains code patterns (matched: {pattern})"

        # Injection check
        for pattern in EnrichmentGuardrail._INJECTION_PATTERNS:
            if re.search(pattern, output, re.IGNORECASE):
                return False, f"Potential prompt injection detected"

        return True, ""


class LLMEnricher:
    """Orchestrates LLM enrichment with guardrails and fallbacks.

    Uses the GitHub Copilot SDK (or any compatible LLM client) for enrichment.
    All enrichment is optional and guarded -- failures fall back to defaults.
    """

    def __init__(self, llm_call: Callable[[str, str], str] | None = None):
        """Initialize with an optional LLM call function.

        Args:
            llm_call: A function(system_prompt, user_prompt) -> str.
                     If None, enrichment is disabled and defaults are used.
        """
        self._llm_call = llm_call
        self._guardrail = EnrichmentGuardrail()

    @property
    def is_enabled(self) -> bool:
        return self._llm_call is not None

    def _is_transient_error(self, exc: Exception) -> bool:
        """Return True for errors that are worth retrying (rate limit, timeout, 5xx)."""
        error_str = str(exc).lower()
        return any(
            signal in error_str
            for signal in ("429", "rate limit", "rate_limit", "timeout", "timed out", "503", "502", "504", "overloaded")
        )

    def enrich(self, target: EnrichmentTarget) -> EnrichmentResult:
        """Attempt to enrich a target, falling back to default on failure."""
        if not self.is_enabled:
            return EnrichmentResult(
                original=target.default_value,
                enriched=target.default_value,
                was_enriched=False,
                target_type=target.target_type,
                rejection_reason="LLM not configured",
            )

        try:
            system_prompt = self._build_system_prompt(target)
            user_prompt = target.context

            raw_output = self._llm_call(system_prompt, user_prompt)

            is_valid, reason = self._guardrail.validate(target, raw_output)
            if is_valid:
                logger.info("llm_enricher.success", target_type=target.target_type.value)
                return EnrichmentResult(
                    original=target.default_value,
                    enriched=raw_output.strip(),
                    was_enriched=True,
                    target_type=target.target_type,
                )
            else:
                logger.warning("llm_enricher.rejected", reason=reason)
                return EnrichmentResult(
                    original=target.default_value,
                    enriched=target.default_value,
                    was_enriched=False,
                    target_type=target.target_type,
                    rejection_reason=reason,
                )

        except Exception as exc:
            if self._is_transient_error(exc):
                logger.info("llm_enricher.transient_error_retry", error=str(exc))
                time.sleep(0.5)
                try:
                    system_prompt = self._build_system_prompt(target)
                    raw_output = self._llm_call(system_prompt, target.context)
                    is_valid, reason = self._guardrail.validate(target, raw_output)
                    if is_valid:
                        logger.info("llm_enricher.retry_succeeded", target_type=target.target_type.value)
                        return EnrichmentResult(
                            original=target.default_value,
                            enriched=raw_output.strip(),
                            was_enriched=True,
                            target_type=target.target_type,
                        )
                except Exception as retry_exc:
                    exc = retry_exc
            logger.warning("llm_enricher.error", error=str(exc))
            return EnrichmentResult(
                original=target.default_value,
                enriched=target.default_value,
                was_enriched=False,
                target_type=target.target_type,
                rejection_reason=f"LLM call failed: {exc}",
            )

    def enrich_batch(self, targets: list[EnrichmentTarget]) -> list[EnrichmentResult]:
        """Enrich multiple targets, returning results in order."""
        return [self.enrich(t) for t in targets]

    def _build_system_prompt(self, target: EnrichmentTarget) -> str:
        """Build a constrained system prompt for the enrichment type."""
        prompts = {
            EnrichmentType.SEED_DESCRIPTION: (
                "You are a technical writer generating realistic seed data descriptions. "
                "Return ONLY a single descriptive sentence. No code, no markdown, no lists. "
                f"Maximum {target.max_length} characters."
            ),
            EnrichmentType.ADR_RATIONALE: (
                "You are a solutions architect writing Architecture Decision Records. "
                "Return ONLY the rationale text explaining why this decision was made. "
                "No code blocks, no headers, no bullet points. Keep it concise. "
                f"Maximum {target.max_length} characters."
            ),
            EnrichmentType.DOC_SECTION: (
                "You are a technical writer improving documentation readability. "
                "Return ONLY the improved text for the section. Maintain the same meaning. "
                "No code, no headers, no formatting changes. "
                f"Maximum {target.max_length} characters."
            ),
            EnrichmentType.ENTITY_DESCRIPTION: (
                "You are a domain expert describing business entities. "
                "Return ONLY a one-sentence description of what this entity represents. "
                f"Maximum {target.max_length} characters."
            ),
            EnrichmentType.THREAT_MITIGATION: (
                "You are a security engineer writing STRIDE threat mitigations. "
                "Return ONLY the mitigation strategy text. Be specific and actionable. "
                f"Maximum {target.max_length} characters."
            ),
            EnrichmentType.UI_COPY: (
                "You are a UX writer creating interface copy for an enterprise application. "
                "Return ONLY the text string. No markup, no quotes, no code. "
                "Be concise, professional, and domain-appropriate. "
                f"Maximum {target.max_length} characters."
            ),
            EnrichmentType.API_DOCSTRING: (
                "You are a technical writer creating API documentation. "
                "Return ONLY a single docstring sentence describing what this endpoint does. "
                "No code, no markdown, no formatting. "
                f"Maximum {target.max_length} characters."
            ),
            EnrichmentType.ERROR_MESSAGE: (
                "You are a UX writer creating user-facing error messages. "
                "Return ONLY the error message text. Be helpful, specific, and professional. "
                "No code, no markdown. "
                f"Maximum {target.max_length} characters."
            ),
            EnrichmentType.SEED_VALUE: (
                "You are generating realistic sample data for an enterprise application. "
                "Return ONLY the data value. No quotes, no explanation, no code. "
                "Be realistic and domain-appropriate. "
                f"Maximum {target.max_length} characters."
            ),
        }
        return prompts.get(target.target_type, f"Return text only. Maximum {target.max_length} characters.")


# ── Convenience factory ──────────────────────────────────────────────

def create_enricher(llm_call: Callable[[str, str], str] | None = None) -> LLMEnricher:
    """Create an LLMEnricher with optional LLM backend.

    When llm_call is None, the enricher is in "pass-through" mode and
    returns deterministic defaults for all enrichment targets.
    """
    return LLMEnricher(llm_call=llm_call)
